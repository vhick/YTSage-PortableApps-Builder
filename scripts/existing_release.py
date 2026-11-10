"""Avoid redundant builds; never mistake unpublished 404 for auth or API failures."""
import json
import os
import sys
from urllib.request import Request,urlopen
from urllib.error import HTTPError
MARKER='<!-- portable-release-publisher:managed:v2 -->'
repo=os.environ['GITHUB_REPOSITORY'];tag=os.environ['RELEASE_TAG']
url=f'https://api.github.com/repos/{repo}/releases/tags/{tag}'
headers={'Accept':'application/vnd.github+json','User-Agent':'YTSagePortable-builder/1.0'}
if os.environ.get('GH_TOKEN'):headers['Authorization']='Bearer '+os.environ['GH_TOKEN']
try:
    with urlopen(Request(url,headers=headers),timeout=40) as r: data=json.load(r)
except HTTPError as e:
    if e.code==404: data=None
    else: raise RuntimeError('Release check HTTP %s - not treated as missing'%e.code) from e
if data:
    if data.get('draft'):raise RuntimeError('Release tag has an incomplete draft; manual inspection required')
    if MARKER not in data.get('body',''):raise RuntimeError('Tag exists but is not publisher-owned')
    if not data.get('assets'):raise RuntimeError('Managed release lacks assets')
    result='true'
else: result='false'
with open(os.environ['GITHUB_OUTPUT'],'a',encoding='utf-8') as f:f.write('exists='+result+'\n')
print('Identical build already published:',result)
