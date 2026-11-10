Builder kit b1r1 local verification evidence (2026-11-10)
========================================================
SOURCE-INSPECTED:  v5.6.0 Python/PySide6 source, constants, FFmpeg code,
                   official Windows cx_Freeze release workflow, license;
                   pinned shared action.yml and installer/publisher scripts.
STATIC-VALIDATED:  Both workflow YAML files parsed with a YAML parser.
STATIC-VALIDATED:  All builder Python scripts pass syntax compileall.
STATIC-VALIDATED:  5 offline unit tests passed (stable numeric tag selection,
                   ZIP-slip rejection, corrupt asset, empty directory ZIP
                   entries and checksum, tampered EXE rejection).
NOT YET VERIFIED:  Download and hash of real v5.6.0 144MB archive in CI.
NOT YET VERIFIED:  MSVC compilation of C++17 YTSagePortable.exe on Windows.
NOT YET VERIFIED:  Real program launch and downloaded helper lifecycle.
NOT YET VERIFIED:  Local user-data containment or installed-app coexistence.
NOT YET VERIFIED:  Windows notifications, OS shell caches, registry changes.
NOT YET VERIFIED:  Actual shared NSIS installer generation/install/upgrade.
NOT YET VERIFIED:  Release Publisher upload/dry-run in calling repository.
NOT YET VERIFIED:  Manual Windows VM acceptance, drive relocation, rollback.
NOT APPLICABLE:   Native-only direct-EXE build, native source patches,
                   native autostart, native work area/appbar integration.

Verification includes controlled synthetic PE headers ONLY inside unittest
fixtures. These are not actual executables and never enter release staging.

No app binaries, Windows launch evidence, installer or published release were
created in this environment. The downloadable artifact is the builder KIT,
which is intended to create those binaries and ZIPs on GitHub Windows runners.
