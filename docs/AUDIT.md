# YTSage v5.6.0 PortableApps-specific upstream audit

Status: **SOURCE-INSPECTED** via canonical upstream GitHub v5.6.0 sources and
release build definitions on 2026-11-10. Later upstream versions MUST be
audited again; the kit fails closed if release structures unexpectedly change.

## Selected mode and binary provenance

Selected **PORTABLEAPPS** only. YTSage is an on-demand Python 3.11-3.14/
PySide6 application; Windows upstream release uses cx_Freeze, not a directly
portable user-data location. Its v5.6.0 official ZIP with FFmpeg is the basis.
Release on 2026-10-14, tag `v5.6.0`, abbreviated source commit `235778d`,
asset `YTSage-v5.6.0-ffmpeg-portable.zip` SHA256
`1955391274348955ae4f4192249cb441842ed416d24800d3a3ac17505ab13339`.
The full 40-character source commit and GitHub asset metadata are verified via
the official GitHub API during every actual build. Prereleases (including
v5.6.3-beta.1) are excluded. The resolver numerically sorts stable tags and
refuses unverified archives.

Dependencies: Python, PySide6/Qt, requests, Pillow, packaging, markdown, loguru,
setuptools; upstream cx_Freeze builds a Windows GUI EXE and bundles the runtime.
FFmpeg and FFprobe are official-release inclusions; yt-dlp and Deno may be
fetched by the application at runtime with upstream hash verification. Source
is MIT; bundled FFmpeg/Qt and other third parties retain their own licenses.
Upstream does not publish a comprehensive lockfile for its PyPI ranges in
`pyproject.toml`; the verified full binary ZIP is the reproducible input rather
than claiming dependency-level reproducibility.

## Findings matrix

| Finding | Source evidence | Host path or registry | Component | NATIVE remedy | PORTABLEAPPS remedy | Data safety | Tradeoff | Test | Limitation |
|---|---|---|---|---|---|---|---|---|---|
| Settings/history/queue/logs/thumbnails | `ytsage/utils/ytsage_constants.py` 83-96, 180+ | `%LOCALAPPDATA%\\YTSage\\...` | Application | N/A | Child-only LOCALAPPDATA=Data/LocalAppData | Does not access old installed profile | None expected | JSON persistence and host snapshot | Framework child paths require runtime observation |
| App's helper binaries | constants 87-97, 151-155; `core/ytsage_yt_dlp.py`; `core/ytsage_deno.py` | `%LOCALAPPDATA%\\YTSage\\bin` | Application | N/A | Same env redirect, keep helper binaries under Data | No host scavenging | First-run may download tools | First/repeat launch, SHA check | Network activity intentionally occurs |
| User download location | `utils/ytsage_config_manager.py` 67-70 | Default user Downloads | Application/user choice | N/A | Initial default `YTSAGE_DOWNLOAD_PATH` = Data/Downloads | User-chosen external folders not collected | Moving the folder can require resetting absolute paths | Change drive letter and confirm | Cached absolute paths can persist |
| FFmpeg updater/setup | `core/ytsage_ffmpeg.py` 205-245, 363-389 | LOCALAPPDATA/ffmpeg and **HKCU User PATH through setx** | Application | N/A | Require bundled FFmpeg + FFprobe; prepend App/YTSage to child PATH before GUI starts | Host PATH untouched by launcher | App's interactive FFmpeg installer should never be needed | ProcMon test no setx/registry change | If app fails to detect bundled FFmpeg, stop usage and fix; no absolute protection against future upstream changes |
| Qt GUI startup and CLI | `ytsage/main.py` 17-30, `setup-scripts/setup_cxfreeze.py` | User-specific Qt/Windows caches unknown | Qt/OS | N/A | Compiled C++17 root launcher before app startup | No broad Qt/APPDATA cleanup | Some Qt/Windows histories may remain | ProcMon and CLI acceptance | NOT runtime-observed |
| Chrome/Firefox cookies | config manager cookie keys 74-80; GUI cookie functionality | Chosen browser user profile | User-authorized | N/A | Do not redirect HOME/USERPROFILE or collect browser cookies | Preserves browser credential protections | Browser cookie import may require installed browser/profile | Browser mode acceptance | User permission, DPAPI portability limits |
| Shortcuts, notification CLSIDs, registry | No source evidence yet of a YTSage-specific registration, no Electron runtime | Any HKCU shell state requires runtime attribution | Windows/framework | N/A | No blind ShellGuard removals | Installed apps protected | Windows-managed caches may remain | Installer-before-runtime snapshot, notifications test | NOT YET VERIFIED |
| Completely empty directories | App directory tree + Data are created by launcher | `Data\\...` | Portable launcher | N/A | Zip writes explicit directory entries; no external moves | Empty Data trees retained on ZIP copy | No host-data harvesting | Fixture test, upgrade/relocation | Installer behavior requires manual acceptance |

Evidence labels: exact source statements are **SOURCE-INSPECTED**. Risk of Qt,
Windows-managed shell traces and installed-app interference is **INFERRED**,
not a claim that it occurs. No registry/shortcut cleanup is included because
there is no established app-owned path that can be safely and selectively
removed. `Data/TraceGuard` is reserved only; not an active scavenger.

## Launcher and package architecture

- A genuine C++17 x64 Windows PE `YTSagePortable.exe` (no batch file, no encoded
  PowerShell at runtime). Includes upstream original icon.
- Before launch, creates Data/LocalAppData/YTSage, Downloads and DenoCache.
- Sets child environment LOCALAPPDATA, DENO_DIR, YTSAGE_DOWNLOAD_PATH,
  YTSAGE_DOWNLOAD_DIR and child PATH. Does not change global/user PATH or
  `%USERPROFILE%`. Existing browser data stays where the user put it.
- Requires bundled FFmpeg/FFprobe; if either is missing it **fails closed**
  rather than letting YTSage invoke its host-mutating installer.
- Forwards arguments, sets the application working directory, prevents duplicate
  launcher starts from the same folder, and uses a Windows job to wait for
  descendants when the OS permits job assignment. No termination-on-launcher-
  close setting, because downloads must not be unexpectedly killed.
- A snapshot of existing installed YTSage data is **not** moved or deleted.
- Uses the pinned `vhick/Portable-Package-Builder@v1.0.0` for independent
  community NSIS installer; the original PortableApps ZIP is independently
  validated first. Uses `vhick/portable-release-publisher@v1.1.1` for the only
  publish step, dry run first; keeps 3, prune=false.
- The ZIP includes Other/Source/BUILD-IDENTITY.json with upstream tag, source
  commit, official binary SHA, local executable SHA, FFmpeg/FFprobe SHA,
  builder repo commit and revision.

## Known limits / unsupported claims

The build kit itself has been statically tested on Linux, but its Windows
launcher compilation, GUI start, Qt user-data containment, FFmpeg PATH behavior,
notification registration, actual NSIS install/upgrade, and GitHub publication
remain **NOT YET VERIFIED** until GitHub Actions and manual Windows acceptance.
This is an unsigned community package; not a genuine PortableApps.com installer.
It is not an application source rebuild; the verified upstream developer
**official portable binary** is used (per the PORTABLEAPPS contract).

No auto-update registration, scheduled task or per-user PATH change is created
by the launcher. The official YTSage GUI may check updates or download yt-dlp
and Deno over the network. Existing custom download-path values can be absolute
and need explicit adjustment after relocation.
