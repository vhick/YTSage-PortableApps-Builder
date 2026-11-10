#!/usr/bin/env python3
"""Independently validate the pinned shared NSIS installer without running GUI.

NSIS File commands embed files relative to SetOutPath, NOT under the final
InstallDir name. 7-Zip often reports .__UPB_Stage/App/... instead of a
YTSagePortable/ top-level directory; check the actual staged payload names.
This is archive/PE/static verification, NOT an installer-execution test.
"""
import argparse
import hashlib
from pathlib import Path
import re
import shutil
import struct
import subprocess
import sys

REQUIRED = (
    'YTSagePortable.exe',
    'App/AppInfo/appinfo.ini',
    'App/YTSage/YTSage.exe',
    'App/YTSage/ffmpeg.exe',
    'App/YTSage/ffprobe.exe',
    'Other/Source/BUILD-IDENTITY.json',
)


def parse_listing(text: str) -> list[str]:
    """Read only actual 7z -slt Path records; ignore archive header metadata."""
    return [m.group(1).strip().replace('\\', '/').rstrip('/')
            for m in re.finditer(r'(?m)^Path = (.+?)\r?$', text)]


def matching_roots(paths: list[str]) -> set[str]:
    """Require every mandatory file in the SAME NSIS-staged payload subtree."""
    roots = None
    for suffix in REQUIRED:
        suffix = suffix.casefold()
        candidates = set()
        for raw in paths:
            path = raw.replace('\\', '/').rstrip('/').casefold()
            if path == suffix:
                candidates.add('')
            elif path.endswith('/' + suffix):
                candidates.add(path[:-(len(suffix) + 1)])
        roots = candidates if roots is None else roots.intersection(candidates)
        if not roots:
            return set()
    return roots or set()


def validate_listing(listing: str) -> str:
    if not re.search(r'(?im)^Type\s*=\s*Nsis(?:\s|$)', listing):
        raise ValueError('7-Zip did not identify this executable as an NSIS archive')
    paths = parse_listing(listing)
    roots = matching_roots(paths)
    if not roots:
        found = ', '.join(sorted(paths)[:12])
        raise ValueError('Installer archive missing a complete YTSagePortable staged '
                         'payload (launcher, AppInfo, app, FFmpeg or build identity). '
                         'First entries: ' + found)
    return min(roots, key=len)


def pe_header(path: Path):
    with path.open('rb') as stream:
        if stream.read(2) != b'MZ':
            raise ValueError('Installer lacks MZ header')
        stream.seek(0x3c)
        offset = struct.unpack('<I', stream.read(4))[0]
        if offset < 64 or offset >= path.stat().st_size - 4:
            raise ValueError('Invalid installer PE offset')
        stream.seek(offset)
        if stream.read(4) != b'PE\x00\x00':
            raise ValueError('Installer lacks PE signature')


def get_7zip() -> str:
    for name in ('7z.exe', '7za.exe', '7zz.exe', '7z', '7za', '7zz'):
        resolved = shutil.which(name)
        if resolved:
            return resolved
    for path in (Path('C:/Program Files/7-Zip/7z.exe'),
                 Path('C:/Program Files (x86)/7-Zip/7z.exe')):
        if path.is_file():
            return str(path)
    raise RuntimeError('7-Zip executable required to inspect NSIS archive')


def run_7z(seven: str, verb: str, path: Path) -> str:
    cmd = [seven, verb]
    if verb == 'l':
        cmd += ['-slt']
    cmd += ['-bsp0', str(path)]
    completed = subprocess.run(cmd, capture_output=True, text=True,
                               encoding='utf-8', errors='replace', timeout=240)
    if completed.returncode != 0:
        raise RuntimeError(f'7-Zip {verb} failed ({completed.returncode}): '
                           f'{completed.stderr[-3000:]} {completed.stdout[-3000:]}')
    return completed.stdout


def verify(path: Path, digest: str):
    if not path.is_file() or path.stat().st_size < 1_000_000:
        raise ValueError('Missing or implausibly small NSIS installer')
    if not path.name.lower().endswith('.paf.exe'):
        raise ValueError('Expected a community PortableApps-style .paf.exe installer')
    if not re.fullmatch(r'[0-9a-fA-F]{64}', digest):
        raise ValueError('Invalid supplied SHA-256')
    with path.open('rb') as stream:
        actual = hashlib.file_digest(stream, 'sha256').hexdigest()
    if actual != digest.lower():
        raise ValueError('Installer SHA-256 does not match shared-builder output')
    pe_header(path)
    seven = get_7zip()
    run_7z(seven, 't', path)
    root = validate_listing(run_7z(seven, 'l', path))
    print(f'STATIC VALIDATED NSIS INSTALLER: {path} SHA256={actual}')
    print(f'7-Zip NSIS payload root: {root or "(archive root)"}')
    print('NOT TESTED: actual installer execution, upgrade, rollback, GUI and Data protection')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--path', required=True)
    parser.add_argument('--sha256', required=True)
    args = parser.parse_args()
    try:
        verify(Path(args.path), args.sha256)
    except Exception as exc:
        sys.exit('INSTALLER VERIFICATION FAILED: ' + str(exc))
