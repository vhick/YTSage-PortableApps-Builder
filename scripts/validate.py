#!/usr/bin/env python3
"""Fail-closed static validation; independent of upstream and shared installer action."""
import argparse
import configparser
import hashlib
import json
from pathlib import Path
import re
import struct
import zipfile

def pe(path):
    with open(path,'rb') as f:
        if f.read(2)!=b'MZ':raise ValueError(f'Not PE/MZ: {path}')
        f.seek(0x3c);off=struct.unpack('<I',f.read(4))[0]
        if not 64<=off<path.stat().st_size-28:raise ValueError(f'Invalid PE header: {path}')
        f.seek(off)
        if f.read(4)!=b'PE\x00\x00':raise ValueError(f'Not PE: {path}')
        machine=struct.unpack('<H',f.read(2))[0]
        if machine!=0x8664:raise ValueError(f'Not 64-bit x64 PE: {path} machine={hex(machine)}')

def validate(root):
    if root.name!='YTSagePortable': raise ValueError('Wrong portable root folder')
    names=['YTSagePortable.exe','App/YTSage/YTSage.exe','App/YTSage/ffmpeg.exe','App/YTSage/ffprobe.exe']
    for name in names:pe(root/name)
    info=root/'App/AppInfo'
    for name in ('appinfo.ini','appicon.ico','appicon_16.png','appicon_32.png'):
        if not (info/name).is_file():raise ValueError('Missing AppInfo '+name)
    if (info/'appicon.ico').read_bytes()[:4]!=b'\x00\x00\x01\x00':raise ValueError('Invalid ICO')
    for size in (16,32):
        if (info/f'appicon_{size}.png').read_bytes()[:8]!=b'\x89PNG\r\n\x1a\n':raise ValueError('Invalid PNG')
    parser=configparser.ConfigParser(interpolation=None)
    parser.read(info/'appinfo.ini',encoding='utf-8')
    for key,value in [('Format','PortableApps.comFormat'),('Control','YTSagePortable.exe')]:
        field='Type' if key=='Format' else 'Start'
        if parser.get(key,field)!=value:raise ValueError(f'Incorrect {key}.{field}')
    if parser.get('Details','AppID')!='YTSageCommunityPortable':raise ValueError('Wrong portable identity')
    if not re.fullmatch(r'\d+\.\d+\.\d+\.\d+',parser.get('Version','PackageVersion')):raise ValueError('Bad version')
    identity=json.loads((root/'Other/Source/BUILD-IDENTITY.json').read_text(encoding='utf-8'))
    if identity['version']+'.0' != parser.get('Version','PackageVersion'):raise ValueError('Version identity mismatch')
    for file,key in [('YTSage.exe','original_executable_sha256'),('ffmpeg.exe','included_ffmpeg_sha256'),('ffprobe.exe','included_ffprobe_sha256')]:
        with (root/'App/YTSage'/file).open('rb') as stream:
            if hashlib.file_digest(stream,'sha256').hexdigest()!=identity[key]:raise ValueError('Binary digest mismatch: '+file)
    for folder in ('App','Data','Other/Source','Data/LocalAppData/YTSage/data','Data/LocalAppData/YTSage/bin',
                   'Data/LocalAppData/YTSage/logs','Data/Downloads','Data/DenoCache'):
        if not (root/folder).is_dir():raise ValueError('Missing data directory: '+folder)
    # No unbounded automatic cleanup, no external host profile transfer.
    for p in root.rglob('*'):
        if p.is_symlink():raise ValueError('Symlink forbidden in staging: '+str(p))
    return identity

def archive(stage, dest):
    root=Path(stage).resolve()
    validate(root)
    dest=Path(dest)
    dest.parent.mkdir(parents=True,exist_ok=True)
    if dest.exists():raise ValueError('Refusing to overwrite package: '+str(dest))
    with zipfile.ZipFile(dest,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=7,allowZip64=True) as z:
        for p in sorted([root]+list(root.rglob('*'))):
            relative=Path(root.name)/p.relative_to(root)
            entry=relative.as_posix()
            if p.is_dir():entry+='/'; payload=b''
            else:payload=None
            i=zipfile.ZipInfo(entry,date_time=(2020,1,1,0,0,0))
            i.compress_type=zipfile.ZIP_DEFLATED
            i.external_attr=((0o40755 if p.is_dir() else 0o100644)<<16)
            if payload is None:
                with p.open('rb') as src,z.open(i,'w',force_zip64=True) as out:
                    import shutil
                    shutil.copyfileobj(src,out,1024*1024)
            else:z.writestr(i,payload)
    with zipfile.ZipFile(dest) as z:
        if z.testzip() is not None:raise ValueError('ZIP CRC validation failed')
        n=set(z.namelist())
        for expected in ('YTSagePortable/YTSagePortable.exe','YTSagePortable/App/AppInfo/appinfo.ini',
                         'YTSagePortable/App/YTSage/YTSage.exe','YTSagePortable/Data/Downloads/'):
            if expected not in n:raise ValueError('Missing archive file/empty folder: '+expected)
    digest=hashlib.sha256(dest.read_bytes()).hexdigest()
    (dest.parent/(dest.name+'.sha256')).write_text(f'{digest}  {dest.name}\n',encoding='ascii')
    print('INDEPENDENT VALIDATED ZIP:',dest,'SHA256:',digest)

def inspect(zip_path,dest):
    with zipfile.ZipFile(zip_path) as z:
        if z.testzip() is not None:raise ValueError('Bad zip CRC')
        for n in z.namelist():
            pieces=Path(n.replace('\\','/')).parts
            if not pieces or pieces[0]!='YTSagePortable' or '..' in pieces or ':' in n:raise ValueError('Unexpected zip path: '+n)
        from stage import safe_extract
        safe_extract(zip_path,dest)
    validate(dest/'YTSagePortable')
    print('Previously validated ZIP re-inspected:',zip_path)

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('mode',choices=['stage','zip','inspect']);a.add_argument('--stage',default='work/stage/YTSagePortable');a.add_argument('--dest');a.add_argument('--zip')
    x=a.parse_args()
    if x.mode=='stage':validate(Path(x.stage));print('VALIDATED staging',x.stage)
    if x.mode=='zip':
        if not x.dest:raise ValueError('Missing --dest');archive(x.stage,x.dest)
    if x.mode=='inspect':
        if not x.dest or not x.zip:raise ValueError('Missing --dest/--zip');inspect(Path(x.zip),Path(x.dest))
