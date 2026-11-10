"""Offline, controlled static fixtures. Synthetic PE headers are NOT working apps."""
import hashlib
import contextlib
import io
import os
import shutil
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
import validate_installer as vi


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
        self.assertIn('call "%YTS_DEV_CMD%" -arch=amd64 -host_arch=amd64',cmd)
        self.assertIn('call "%~dp0msvc_env.cmd"',build)
        self.assertIn('rc.exe /nologo /fo"%YTS_RESOURCE%"',build)
        self.assertIn('subprocess.run([str(script)]',Path(__file__).read_text(encoding='utf-8'))

    @unittest.skipUnless(sys.platform == 'win32', 'Real MSVC test requires a Windows runner')
    def test_real_cmd_vscmd_spaced_path_and_missing_path(self):
        # b1r3's synthetic VsDevCmd stub failed with exit 11, but the test
        # suppressed the command's diagnostics. Do not mistake a fake .bat
        # for MSVC. Check the ACTUAL compiler installation used by CI.
        scripts=Path(__file__).resolve().parent.parent/'scripts'
        original=scripts/'msvc_env.cmd'
        vswhere=Path(os.environ['ProgramFiles(x86)'])/'Microsoft Visual Studio'/'Installer'/'vswhere.exe'
        self.assertTrue(vswhere.is_file(),f'vswhere.exe missing: {vswhere}')
        found=subprocess.run([str(vswhere),'-latest','-products','*',
                              '-requires','Microsoft.VisualStudio.Component.VC.Tools.x86.x64',
                              '-property','installationPath'],capture_output=True,
                             text=True,timeout=30)
        self.assertEqual(found.returncode,0,found.stdout+'\n'+found.stderr)
        self.assertTrue(found.stdout.strip(),'No Visual Studio instance with C++ x64 tools')
        devcmd=Path(found.stdout.strip())/'Common7'/'Tools'/'VsDevCmd.bat'
        self.assertTrue(devcmd.is_file(),f'VsDevCmd.bat missing: {devcmd}')
        with tempfile.TemporaryDirectory(prefix='YTSage VS Cmd ') as d:
            script=Path(d)/'Builder Kit With Spaces'/'msvc_env.cmd'
            script.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(original,script)
            # This batch invokes the reviewed msvc_env.cmd just like
            # launcher-build.cmd and verifies the compiler tools really load.
            caller=script.parent/'verify-real-toolchain.cmd'
            caller.write_bytes((
                '@echo off\r\n'
                'call "%~dp0msvc_env.cmd"\r\n'
                'if errorlevel 1 exit /b 55\r\n'
                'where.exe cl.exe >nul 2>nul\r\n'
                'if errorlevel 1 exit /b 56\r\n'
                'where.exe rc.exe >nul 2>nul\r\n'
                'if errorlevel 1 exit /b 57\r\n'
                'exit /b 0\r\n'
            ).encode('ascii'))
            environment=os.environ.copy()
            environment['YTS_DEV_CMD']=str(devcmd)
            result=subprocess.run([str(caller)],env=environment,cwd=d,
                                  capture_output=True,text=True,timeout=90)
            self.assertEqual(result.returncode,0,
                             f'Actual VS devcmd failed ({result.returncode}):\n{result.stdout}\n{result.stderr}')
            # Confirm the PowerShell call operator used by build_launcher.ps1.
            environment['YTS_TEST_SCRIPT']=str(caller)
            powershell=subprocess.run(['pwsh','-NoProfile','-NonInteractive','-Command',
                                      '& $env:YTS_TEST_SCRIPT; exit $LASTEXITCODE'],
                                     env=environment,cwd=d,capture_output=True,text=True,timeout=90)
            self.assertEqual(powershell.returncode,0,
                             f'PowerShell launch failed:\n{powershell.stdout}\n{powershell.stderr}')
            # Negative-path assertions retain the exact stable status codes.
            environment.pop('YTS_DEV_CMD')
            missing=subprocess.run([str(script)],env=environment,cwd=d,
                                   capture_output=True,text=True,timeout=20)
            self.assertEqual(missing.returncode,31,missing.stdout+'\n'+missing.stderr)
            environment['YTS_DEV_CMD']=str(Path(d)/'missing'/'VsDevCmd.bat')
            stale=subprocess.run([str(script)],env=environment,cwd=d,
                                 capture_output=True,text=True,timeout=20)
            self.assertEqual(stale.returncode,32,stale.stdout+'\n'+stale.stderr)

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
            target=Path(d)/'out'/'YTSagePortable_5.6.0_b1r5.zip'
            # This is a synthetic fixture, not a distributable app build.
            # Suppress the production archive log to prevent misleading CI output.
            with contextlib.redirect_stdout(io.StringIO()):
                validate.archive(root,target)
            with zipfile.ZipFile(target) as z:
                self.assertIn('YTSagePortable/Data/Downloads/',z.namelist())
                self.assertIn('YTSagePortable/Data/TraceGuard/',z.namelist())
                self.assertIsNone(z.testzip())
            self.assertTrue(target.with_name(target.name+'.sha256').is_file())
            with self.assertRaises(ValueError):validate.archive(root,target)
    def test_actual_validate_cli_zip_and_inspect(self):
        """Regression: b1r4's CLI returned zero but never created a ZIP.

        Exercise the real command-line dispatch and validate the resulting
        disk file, not merely a direct call of archive().
        """
        with tempfile.TemporaryDirectory(prefix='YTSage test path with spaces ') as d:
            directory = Path(d)
            root = directory/'YTSagePortable'
            fixture(root)
            archive = directory/'out'/'YTSagePortable_5.6.0_b1r5.zip'
            script = Path(validate.__file__)
            command = subprocess.run([sys.executable, str(script), 'zip', '--stage',
                                      str(root), '--dest', str(archive)],
                                     capture_output=True, text=True, timeout=30)
            self.assertEqual(command.returncode, 0, command.stderr + command.stdout)
            self.assertIn('INDEPENDENT VALIDATED ZIP:', command.stdout)
            self.assertTrue(archive.is_file(), 'CLI did not create ZIP')
            self.assertTrue(archive.with_name(archive.name + '.sha256').is_file())
            self.assertGreater(archive.stat().st_size, 0)
            unpack = directory/'reconstituted with spaces'
            command = subprocess.run([sys.executable, str(script), 'inspect',
                                      '--zip', str(archive), '--dest', str(unpack)],
                                     capture_output=True, text=True, timeout=30)
            self.assertEqual(command.returncode, 0, command.stderr + command.stdout)
            self.assertIn('Previously validated ZIP re-inspected:', command.stdout)
            self.assertTrue((unpack/'YTSagePortable'/'YTSagePortable.exe').is_file())
            self.assertTrue((unpack/'YTSagePortable'/'Data'/'Downloads').is_dir())

    def test_nsis_payload_paths_relative_to_staging_not_installdir(self):
        """Regression: NSIS installs a staged subtree, NOT the final folder."""
        for prefix in ('', 'YTSagePortable/', '.__UPB_Stage/',
                       '$INSTDIR\\.__UPB_Stage\\'):
            paths = '\n'.join('Path = ' + prefix + suffix.replace('/', '\\')
                              for suffix in vi.REQUIRED)
            listing = 'Path = installer.paf.exe\nType = Nsis\n\n' + paths
            self.assertEqual(vi.validate_listing(listing),
                             prefix.replace('\\', '/').rstrip('/').casefold())

    def test_nsis_payload_validation_fail_closed(self):
        source = 'Path = installer.paf.exe\nType = Nsis\n\n'
        listing = source + '\n'.join('Path = .__UPB_Stage/' + p
                                    for p in vi.REQUIRED)
        self.assertEqual(vi.validate_listing(listing), '.__upb_stage')
        bad_missing = listing.replace('Path = .__UPB_Stage/App/YTSage/ffprobe.exe', '')
        with self.assertRaises(ValueError):
            vi.validate_listing(bad_missing)
        with self.assertRaises(ValueError):
            vi.validate_listing(listing.replace('Type = Nsis', 'Type = zip'))
        # Same paths split across different payload roots must be rejected.
        mismatched = listing.replace('Path = .__UPB_Stage/App/YTSage/ffmpeg.exe',
                                     'Path = OtherApp/App/YTSage/ffmpeg.exe')
        with self.assertRaises(ValueError):
            vi.validate_listing(mismatched)

    def test_installer_only_accepts_new_managed_builder_revision(self):
        """Regression: b1r4 repackage regex excluded its own release tag."""
        script = Path(__file__).resolve().parent.parent/'scripts'/'repackage.py'
        with tempfile.TemporaryDirectory() as d:
            outputs = Path(d)/'output.txt'
            env = dict(os.environ,
                       SOURCE_RELEASE='portable-ytsage-v5.6.5-b1r5-u2c564ac5-b1863ed42',
                       NEW_REV='r2', GITHUB_SHA='a'*40, GITHUB_OUTPUT=str(outputs))
            result = subprocess.run([sys.executable, str(script), 'tag'],
                                    env=env, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn('-installer-r2-baaaaaaaa', outputs.read_text())
            env['SOURCE_RELEASE'] = 'portable-unrelated-v5.6.5-b1r5-u2c564ac5-b1863ed42'
            bad = subprocess.run([sys.executable, str(script), 'tag'],
                                 env=env, capture_output=True, text=True)
            self.assertNotEqual(bad.returncode, 0)

    def test_rejects_modified_app_executable(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/'YTSagePortable';fixture(root)
            (root/'App/YTSage/YTSage.exe').write_bytes(b'tampered')
            with self.assertRaises(ValueError):validate.validate(root)

if __name__=='__main__':unittest.main()
