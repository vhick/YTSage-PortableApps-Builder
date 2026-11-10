#!/usr/bin/env python3
"""Stage the exact official binary into a PortableApps root. No downloaded executable is run in CI."""
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import stat
import sys
import zipfile

ROOT=Path(__file__).resolve().parent.parent
OUT=Path('work/stage/YTSagePortable')

def sha(path):
    with open(path,'rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()

def safe_extract(zip_path, out):
    with zipfile.ZipFile(zip_path) as z:
        members=z.infolist()
        if sum(m.file_size for m in members)>2_000_000_000: raise ValueError('Uncompressed archive too large')
        for member in members:
            raw=member.filename.replace('\\','/')
            p=PurePosixPath(raw)
            if p.is_absolute() or '..' in p.parts or ':' in raw or not raw or '\x00' in raw:
                raise ValueError('Unsafe ZIP path: '+raw)
            if (member.external_attr >> 16) & 0o170000 == stat.S_IFLNK:
                raise ValueError('Symlink in upstream ZIP: '+raw)
            target=out.joinpath(*p.parts)
            if member.is_dir(): target.mkdir(parents=True,exist_ok=True)
            else:
                target.parent.mkdir(parents=True,exist_ok=True)
                with z.open(member) as src, target.open('wb') as dst: shutil.copyfileobj(src,dst,1024*1024)

def appinfo(version):
    parts=[int(p) for p in version.split('.')]
    return f'''[Format]
Type=PortableApps.comFormat
Version=3.8

[Details]
Name=YTSage Portable (Community)
AppID=YTSageCommunityPortable
Publisher=oop7 (upstream); community packaging
Homepage=https://github.com/oop7/YTSage
Category=Internet
Description=YouTube downloader with PySide6 and yt-dlp
Language=Multilingual
Trademarks=YTSage is an upstream project; this package is unofficial

[License]
Shareable=true
OpenSource=true
Freeware=true
CommercialUse=true
EULAVersion=1

[Version]
PackageVersion={parts[0]}.{parts[1]}.{parts[2]}.0
DisplayVersion={version} Community b1r1

[Control]
Icons=1
Start=YTSagePortable.exe

[Associations]

'''

def main():
    meta=json.loads(Path('work/upstream.json').read_text(encoding='utf-8'))
    up=Path('work/upstream_source')
    if not (up/'.git').is_dir(): raise ValueError('Exact pinned upstream source checkout missing')
    # run git through subprocess so we never confuse latest main with the chosen tag.
    import subprocess
    proc=subprocess.run(['git','-C',str(up),'rev-parse','HEAD'],capture_output=True,text=True,check=True)
    if proc.stdout.strip().lower()!=meta['upstream_commit']:
        raise ValueError('Source checkout does not match tag commit')
    if sha(Path('work')/meta['upstream_asset']) != meta['upstream_asset_sha256']:
        raise ValueError('Upstream release binary SHA mismatch')
    if OUT.exists(): shutil.rmtree(OUT)
    app=OUT/'App/YTSage'; app.mkdir(parents=True)
    safe_extract(Path('work')/meta['upstream_asset'],app)
    # Official ZIP is flat in the audited 5.6.0 workflow. No guessing about nested archives.
    official=app/f'YTSage-v{meta["version"]}-ffmpeg.exe'
    if not official.is_file(): raise ValueError('Upstream FFmpeg executable missing or upstream layout changed')
    official.rename(app/'YTSage.exe')
    for name in ('ffmpeg.exe','ffprobe.exe'):
        if not (app/name).is_file(): raise ValueError('Bundled '+name+' missing; refuse PATH modification risk')
    icon=up/'branding/icons/YTSage.ico'
    if not icon.is_file() or icon.stat().st_size<100: raise ValueError('Authentic upstream icon missing')
    info=OUT/'App/AppInfo'; info.mkdir(parents=True)
    shutil.copy2(icon,info/'appicon.ico')
    from PIL import Image  # Build-only dependency installed after offline regression tests.
    with Image.open(icon) as im:
        for size in (16,32):
            im.resize((size,size),Image.Resampling.LANCZOS).save(info/f'appicon_{size}.png')
    (info/'appinfo.ini').write_text(appinfo(meta['version']),encoding='utf-8',newline='\n')
    (info/'Launcher').mkdir()
    (info/'Launcher'/'README.txt').write_text('Custom compiled launcher is at the package root. No PortableApps.com Launcher INI is used.\n',encoding='utf-8')
    for sub in ('LocalAppData/YTSage/data','LocalAppData/YTSage/logs','LocalAppData/YTSage/bin',
                'Downloads','DenoCache','TraceGuard'):
        (OUT/'Data'/sub).mkdir(parents=True,exist_ok=True)
    other=OUT/'Other/Source';other.mkdir(parents=True)
    shutil.copy2(ROOT/'launcher/YTSagePortable.cpp',other/'YTSagePortable.cpp')
    shutil.copy2(ROOT/'LICENSES/LAUNCHER-MIT.txt',other/'LAUNCHER-LICENSE.txt')
    shutil.copy2(up/'LICENSE',other/'YTSage-LICENSE.txt')
    shutil.copy2(ROOT/'docs/RUNTIME-ACCEPTANCE.md',other/'RUNTIME-ACCEPTANCE.txt')
    readme=ROOT/'docs/PORTABLE-PACKAGE-README.md'
    shutil.copy2(readme,OUT/'README.txt')
    meta.update(builder_commit=os.environ.get('GITHUB_SHA',''),
                source_pyproject_sha256=sha(up/'pyproject.toml'),
                source_license_sha256=sha(up/'LICENSE'),
                original_executable_sha256=sha(app/'YTSage.exe'),
                included_ffmpeg_sha256=sha(app/'ffmpeg.exe'),
                included_ffprobe_sha256=sha(app/'ffprobe.exe'),
                icon_sha256=sha(icon),
                portable_strategy='child-localappdata-env-with-bundled-ffmpeg')
    (other/'BUILD-IDENTITY.json').write_text(json.dumps(meta,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print('Staged official YTSage',meta['version'],'under',OUT)
if __name__=='__main__':
    try: main()
    except Exception as exc: sys.exit('STAGING FAILED: '+str(exc))
