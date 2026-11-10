"""Repackage only signed-off, same-repository ZIP packages; no rebuild of upstream."""
import hashlib
import os
from pathlib import Path
import re
import sys

def main():
    source=os.environ['SOURCE_RELEASE']
    revision=os.environ['NEW_REV']
    if not re.fullmatch(r'portable-ytsage-v\d+\.\d+\.\d+-b1r(?:1|2)-u[0-9a-f]{8}-b[0-9a-f]{8}',source):
        raise ValueError('Use a full b1r1/b1r2 builder-managed YTSage tag, not another project/repack tag')
    if not re.fullmatch(r'r[2-9][0-9]*',revision):
        raise ValueError('New package revision must be r2, r3, etc.')
    action=sys.argv[1]
    if action=='tag':
        sha=os.environ['GITHUB_SHA']
        if not re.fullmatch(r'[0-9a-fA-F]{40}',sha):raise ValueError('Missing builder commit')
        tag=f'{source}-installer-{revision}-b{sha[:8].lower()}'
        with open(os.environ['GITHUB_OUTPUT'],'a',encoding='utf-8') as f:f.write('tag='+tag+'\n')
        print('New independent release:',tag)
        return
    if action=='verify':
        folder=Path('work/from_release')
        zips=list(folder.glob('*.zip'))
        if len(zips)!=1:raise ValueError('Expected exactly one trusted original ZIP')
        manifest=(folder/'SHA256SUMS.txt').read_text(encoding='utf-8')
        records=[]
        for line in manifest.splitlines():
            m=re.fullmatch(r'([0-9a-fA-F]{64})\s+([^/\\]+)',line.strip())
            if m:records.append((m[2],m[1].lower()))
        expected=dict(records).get(zips[0].name)
        if not expected:raise ValueError('Original ZIP not listed in trusted release manifest')
        with zips[0].open('rb') as stream:actual=hashlib.file_digest(stream,'sha256').hexdigest()
        if actual!=expected:raise ValueError('Original ZIP sha256 does not match release')
        print('Trusted published ZIP SHA256 VERIFIED:',actual)
        return
    raise ValueError('Invalid action')
if __name__=='__main__':
    try:main()
    except Exception as e:sys.exit('REPACKAGE FAILED: '+str(e))
