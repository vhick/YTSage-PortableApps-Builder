"""Fail if key upstream YTSage portability assumptions stop being true.
This is a narrow regression guard, not a replacement for human release auditing.
"""
from pathlib import Path
import sys
root=Path('work/upstream_source')
checks={
    'ytsage/utils/ytsage_constants.py': [
        'os.environ.get("LOCALAPPDATA"',
        'APP_DIR / "bin"',
        'APP_DIR / "data"',
        'APP_DIR / "logs"',
        'APP_DATA_DIR / "ytsage_config.json"',
        'APP_DATA_DIR / "ytsage_history.json"',
        'APP_DATA_DIR / "ytsage_download_queue.json"',
        'APP_BIN_DIR / "deno.exe"',
    ],
    'ytsage/core/ytsage_ffmpeg.py': [
        'def check_ffmpeg_installed()',
        '["ffmpeg", "-version"]',
        '["setx", "PATH", new_path]',
    ],
    'ytsage/utils/ytsage_config_manager.py': [
        'YTSAGE_DOWNLOAD_PATH',
        'YTSAGE_DOWNLOAD_DIR',
    ],
    'setup-scripts/setup_cxfreeze.py': [
        'YTSAGE_EXECUTABLE_SUFFIX',
        'target_name=f"YTSage-v{version}{suffix}.exe"',
    ],
}
for filename,needles in checks.items():
    p=root/filename
    if not p.is_file():sys.exit('Upstream portability audit failed; missing: '+filename)
    source=p.read_text(encoding='utf-8')
    for needle in needles:
        if needle not in source:sys.exit('Upstream portability audit changed: '+filename+' : '+needle)
# New system PATH mutations are not treated as safe just because bundled FFmpeg exists.
for p in (root/'ytsage').rglob('*.py'):
    content=p.read_text(encoding='utf-8')
    if 'setx' in content and p.as_posix().replace('\\','/').split('ytsage/',1)[-1]!='core/ytsage_ffmpeg.py':
        sys.exit('New source file invokes setx: '+str(p))
print('SOURCE-INSPECTED invariants confirmed; interactive Windows audit remains required')
