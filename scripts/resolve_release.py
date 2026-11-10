#!/usr/bin/env python3
"""Resolve a GitHub YTSage stable release and its official FFmpeg portable binary.
Refuse assets without vendor-published SHA256 or an explicitly reviewed pinned hash.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

REPO = 'oop7/YTSage'
API = 'https://api.github.com/repos/' + REPO
# Vendor-published digest visible on the upstream v5.6.0 release (2026-10-14).
# This is an exact filename/version exception, NOT a general trust bypass.
REVIEWED_SHA = {
    'YTSage-v5.6.0-ffmpeg-portable.zip': '1955391274348955ae4f4192249cb441842ed416d24800d3a3ac17505ab13339',
}
TAG = re.compile(r'^v(\d+)\.(\d+)\.(\d+)$')
SHA = re.compile(r'^[0-9a-fA-F]{64}$')
COMMIT = re.compile(r'^[0-9a-fA-F]{40}$')

def api(path):
    headers = {'Accept': 'application/vnd.github+json',
               'User-Agent': 'YTSagePortable-builder/1.0',
               'X-GitHub-Api-Version': '2022-11-28'}
    token = os.getenv('GH_TOKEN', '')
    if token:
        headers['Authorization'] = 'Bearer ' + token
    req = Request(API + path, headers=headers)
    try:
        with urlopen(req, timeout=40) as response:
            return json.load(response)
    except HTTPError as exc:
        # Never convert permission, rate-limit, or server faults into a missing release.
        if exc.code == 404:
            raise ValueError('Upstream API item not found (HTTP 404): ' + path) from exc
        raise RuntimeError('GitHub API HTTP %d for %s' % (exc.code, path)) from exc
    except URLError as exc:
        raise RuntimeError('GitHub API connection failed: ' + str(exc)) from exc

def version_key(release):
    match = TAG.fullmatch(release.get('tag_name', ''))
    return tuple(int(i) for i in match.groups()) if match else None

def select_release(version):
    if version != 'latest':
        if not TAG.fullmatch(version):
            raise ValueError('Only stable release tags vMAJOR.MINOR.PATCH are accepted')
        record = api('/releases/tags/' + version)
        if record.get('draft') or record.get('prerelease'):
            raise ValueError('Requested release is not stable')
        return record
    stable = []
    for page in range(1, 11):
        items = api(f'/releases?per_page=100&page={page}')
        if not isinstance(items, list):
            raise RuntimeError('GitHub release listing response was not an array')
        stable.extend(r for r in items if not r.get('draft') and not r.get('prerelease') and version_key(r))
        if len(items) < 100:
            break
    if not stable:
        raise RuntimeError('No suitable stable YTSage releases found')
    return max(stable, key=version_key)

def resolve_commit(tag):
    obj = api('/git/ref/tags/' + tag).get('object', {})
    for _ in range(3):
        if obj.get('type') == 'commit':
            value = obj.get('sha', '')
            if not COMMIT.fullmatch(value):
                raise ValueError('Invalid upstream commit SHA')
            return value.lower()
        if obj.get('type') != 'tag' or not COMMIT.fullmatch(obj.get('sha', '')):
            raise ValueError('Tag does not refer to an expected git object')
        obj = api('/git/tags/' + obj['sha']).get('object', {})
    raise ValueError('Unexpected deeply nested annotated tag')

def resolve(version):
    release = select_release(version)
    tag = release['tag_name']
    version_str = tag[1:]
    name = f'YTSage-v{version_str}-ffmpeg-portable.zip'
    matches = [a for a in release.get('assets', []) if a.get('name') == name]
    if len(matches) != 1:
        raise ValueError('Missing or ambiguous official FFmpeg portable ZIP asset: ' + name)
    asset = matches[0]
    digest = asset.get('digest') or ''
    if digest.startswith('sha256:'):
        digest = digest[7:]
    if not digest:
        digest = REVIEWED_SHA.get(name, '')
    if not SHA.fullmatch(digest):
        raise ValueError('Missing trusted SHA256 for ' + name + '; review upstream before building')
    if not (1_000_000 < int(asset.get('size') or 0) < 2_000_000_000):
        raise ValueError('Official asset size is implausible')
    url = asset.get('browser_download_url', '')
    if url != f'https://github.com/oop7/YTSage/releases/download/{tag}/{name}':
        raise ValueError('Unexpected official asset URL')
    commit = resolve_commit(tag)
    return dict(tag=tag, version=version_str, upstream_commit=commit,
                upstream_asset=name, upstream_asset_url=url,
                upstream_asset_sha256=digest.lower(), upstream_asset_size=asset['size'],
                upstream_release_id=release['id'], builder_revision='b1r3',
                packaging_revision='r1', source='official-developer-ffmpeg-portable-zip')

def main():
    version = os.getenv('UPSTREAM_VERSION', 'latest').strip() or 'latest'
    result = resolve(version)
    folder = Path('work')
    folder.mkdir(exist_ok=True)
    (folder / 'upstream.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    package_version = result['version']
    builder_sha = os.getenv('GITHUB_SHA', '').strip()
    if not COMMIT.fullmatch(builder_sha):
        raise ValueError('Expected a real builder GITHUB_SHA commit')
    short_builder = builder_sha[:8].lower()
    short_upstream = result['upstream_commit'][:8]
    tag = f'portable-ytsage-v{package_version}-b1r3-u{short_upstream}-b{short_builder}'
    with open(os.environ['GITHUB_OUTPUT'], 'a', encoding='utf-8', newline='\n') as out:
        for key, value in (('tag', tag), ('upstream_tag', result['tag']),
                           ('upstream_sha', result['upstream_commit']), ('version', package_version)):
            out.write(key + '=' + value + '\n')
    print('Selected', result['tag'], result['upstream_commit'], result['upstream_asset'])
    print('Official ZIP SHA256:', result['upstream_asset_sha256'])
    print('Builder release tag:', tag)

if __name__ == '__main__':
    try:
        main()
    except (ValueError, RuntimeError, KeyError, OSError) as exc:
        sys.exit('RELEASE RESOLUTION FAILED: ' + str(exc))
