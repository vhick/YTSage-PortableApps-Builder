#!/usr/bin/env python3
"""Download an exact verified GitHub release asset, with bounds and atomic rename."""
import hashlib
import json
from pathlib import Path
import os
import sys
from urllib.request import Request, urlopen

def main():
    meta=json.loads(Path('work/upstream.json').read_text(encoding='utf-8'))
    path=Path('work')/meta['upstream_asset']
    tmp=path.with_suffix(path.suffix+'.part')
    if path.exists():
        with path.open('rb') as cached:
            cached_sha=hashlib.file_digest(cached,'sha256').hexdigest()
        if cached_sha==meta['upstream_asset_sha256']:
            print('Trusted verified cache:', path)
            return
    path.unlink(missing_ok=True)
    tmp.unlink(missing_ok=True)
    request=Request(meta['upstream_asset_url'], headers={'User-Agent':'YTSagePortable-builder/1.0'})
    digest=hashlib.sha256()
    total=0
    try:
        with urlopen(request, timeout=180) as r, tmp.open('wb') as dst:
            while True:
                chunk=r.read(1024*1024)
                if not chunk: break
                total+=len(chunk)
                if total>2_000_000_000: raise ValueError('Download exceeds maximum size')
                digest.update(chunk)
                dst.write(chunk)
        if total != meta['upstream_asset_size']:
            raise ValueError(f'Asset size mismatch: got {total}, expected {meta["upstream_asset_size"]}')
        if digest.hexdigest().lower() != meta['upstream_asset_sha256']:
            raise ValueError('OFFICIAL UPSTREAM ASSET SHA256 MISMATCH')
        tmp.replace(path)
    except Exception:
        tmp.unlink(missing_ok=True)
        raise
    print('Verified upstream ZIP:',path, 'SHA256:',digest.hexdigest())
if __name__ == '__main__':
    try: main()
    except Exception as exc: sys.exit('DOWNLOAD FAILED: '+str(exc))
