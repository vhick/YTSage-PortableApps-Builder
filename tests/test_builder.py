"""Offline, controlled static fixtures. Synthetic PE headers are NOT working apps."""
import hashlib
import os
import subprocess
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest
import zipfile

sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'scripts'))
import resolve_release as rr
import stage
import validate


def synthetic_pe(path):
    # Static validation fixture ONLY. Never distributed as a package executable.
    b=bytearray(128)
    b[:2]=b'MZ'
    struct.pack_into('<I',b,0x3c,64)
    b[64:68]=b'PE\x00\x00'
    struct.pack_into('<H',b,68,0x8664)
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_bytes(b)

def fixture(root):
    for name in ['YTSagePortable.exe','App/YTSage/YTSage.exe','App/YTSage/ffmpeg.exe','App/YTSage/ffprobe.exe']:
        synthetic_pe(root/name)
    info=root/'App/AppInfo'
    info.mkdir(parents=True,exist_ok=True)
    (info/'appinfo.ini').write_text(stage.appinfo('5.6.0'),encoding='utf-8')
    (info/'appicon.ico').write_bytes(b'\x00\x00\x01\x00'+b'\x00'*100)
    for size in (16,32):
        (info/f'appicon_{size}.png').write_bytes(b'\x89PNG\r\n\x1a\nfixture')
    for directory in ('Data/LocalAppData/YTSage/data','Data/LocalAppData/YTSage/bin',
                      'Data/LocalAppData/YTSage/logs','Data/Downloads','Data/DenoCache',
                      'Data/TraceGuard','Other/Source'):
        (root/directory).mkdir(parents=True,exist_ok=True)
    identity={'version':'5.6.0'}
    for name,key in [('YTSage.exe','original_executable_sha256'),('ffmpeg.exe','included_ffmpeg_sha256'),('ffprobe.exe','included_ffprobe_sha256')]:
        identity[key]=hashlib.sha256((root/'App/YTSage'/name).read_bytes()).hexdigest()
    (root/'Other/Source/BUILD-IDENTITY.json').write_text(json.dumps(identity),encoding='utf-8')

class OfflineTests(unittest.TestCase):
    def test_batch_msvc_command_not_split_by_powershell(self):
        # b1r1 broke because the PowerShell @() list split a quoted path into
        # three batch commands: '"', 'C:\Program', and '" -arch=...'.
        scripts=Path(__file__).resolve().parent.parent/'scripts'
        ps=(scripts/'build_launcher.ps1').read_text(encoding='utf-8')
        cmd=(scripts/'msvc_env.cmd').read_text(encoding='ascii')
        build=(scripts/'launcher-build.cmd').read_text(encoding='ascii')
        self.assertNotIn("'call \"' + $devcmd",ps)
        self.assertIn('$env:YTS_DEV_CMD = $devcmd',ps)
        self.assertIn('call "%YTS_DEV_CMD%" -arch=amd64 -host_arch=amd64 >nul',cmd)
        self.assertIn('call "%~dp0msvc_env.cmd"',build)
        self.assertIn('rc.exe /nologo /fo"%YTS_RESOURCE%"',build)

    @unittest.skipUnless(sys.platform == 'win32', 'Windows CMD requires Windows runner')
    def test_real_cmd_vscmd_spaced_path_and_missing_path(self):
        # Exercise the REAL production msvc_env.cmd against a harmless fake
        # VsDevCmd.bat, deliberately located under a directory with spaces.
        script=Path(__file__).resolve().parent.parent/'scripts/msvc_env.cmd'
        with tempfile.TemporaryDirectory(prefix='YTSage VS Cmd ') as d:
            fake=Path(d)/'Program Files'/ 'Microsoft Visual Studio' / 'Common7' / 'Tools' / 'VsDevCmd.bat'
            fake.parent.mkdir(parents=True,exist_ok=True)
            fake.write_bytes(b'@echo off\r\nif not "%~1"=="-arch=amd64" exit /b 71\r\nif not "%~2"=="-host_arch=amd64" exit /b 72\r\nexit /b 0\r\n')
            environment=os.environ.copy()
            environment['YTS_DEV_CMD']=str(fake)
            result=subprocess.run(['cmd.exe','/d','/c',f'call "{script}"'],env=environment,cwd=d,capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stdout+'\n'+result.stderr)
            environment.pop('YTS_DEV_CMD')
            result=subprocess.run(['cmd.exe','/d','/c',f'call "{script}"'],env=environment,cwd=d,capture_output=True,text=True)
            self.assertEqual(result.returncode,31,result.stdout+'\n'+result.stderr)
    def test_numeric_stable_selection(self):
        old=rr.api
        try:
            rr.api=lambda p:[{'tag_name':'v5.9.0','draft':False,'prerelease':False},
                             {'tag_name':'v5.10.0','draft':False,'prerelease':False},
                             {'tag_name':'v5.12.0-beta.1','draft':False,'prerelease':True}]
            self.assertEqual(rr.select_release('latest')['tag_name'],'v5.10.0')
            with self.assertRaises(ValueError):rr.select_release('v6.0.0-beta.1')
        finally:rr.api=old
    def test_safe_extract_blocks_parent_escape(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'bad.zip'
            with zipfile.ZipFile(p,'w') as z:z.writestr('../outside.txt','bad')
            with self.assertRaises(ValueError):stage.safe_extract(p,Path(d)/'dest')
            self.assertFalse((Path(d)/'outside.txt').exists())
    def test_early_failure_on_corrupt_upstream_asset(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'bad.zip'
            p.write_bytes(b'not a valid archive')
            with self.assertRaises(zipfile.BadZipFile):stage.safe_extract(p,Path(d)/'dest')
    def test_zip_explicit_empty_folders_and_checksums(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/'YTSagePortable'
            fixture(root)
            validate.validate(root)
            target=Path(d)/'out'/'YTSagePortable_5.6.0_b1r2.zip'
            validate.archive(root,target)
            with zipfile.ZipFile(target) as z:
                self.assertIn('YTSagePortable/Data/Downloads/',z.namelist())
                self.assertIn('YTSagePortable/Data/TraceGuard/',z.namelist())
                self.assertIsNone(z.testzip())
            self.assertTrue(target.with_name(target.name+'.sha256').is_file())
            with self.assertRaises(ValueError):validate.archive(root,target)
    def test_rejects_modified_app_executable(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/'YTSagePortable';fixture(root)
            (root/'App/YTSage/YTSage.exe').write_bytes(b'tampered')
            with self.assertRaises(ValueError):validate.validate(root)

if __name__=='__main__':unittest.main()
