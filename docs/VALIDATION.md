Builder kit b1r4 local verification evidence (2026-11-10)
========================================================
SOURCE-INSPECTED:  v5.6.0 Python/PySide6 source, constants, FFmpeg code,
                   official Windows cx_Freeze release workflow, license;
                   pinned shared action.yml and installer/publisher scripts.
STATIC-VALIDATED:  Both workflow YAML files parsed with a YAML parser.
STATIC-VALIDATED:  All builder Python scripts pass syntax compileall.
STATIC-VALIDATED:  6 cross-platform offline unit tests passed (stable numeric tag selection,
                   ZIP-slip rejection, corrupt asset, empty directory ZIP
                   entries and checksum, tampered EXE rejection).
GITHUB-ACTIONS-OBSERVED (b1r1):  Real official archive downloaded and hash-verified before Step 11 failure.
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

Observed from user-supplied GitHub Actions run logs (2026-11-10, b1r1):
WINDOWS-CI-OBSERVED:  release selection, checked-out source, hash-verified
                      official asset download, staging and prior regressions
                      succeeded before launcher build.
FAILED/BLOCKED:       b1r1 Step 11 batch quoting split VsDevCmd path;
                      developer environment command failed with code 11.
STATIC-VALIDATED:     b1r2 correction avoided dynamic batch assembly,
                      but the b1r2 Windows test had the invocation defect.
NOT YET VERIFIED:     b1r4 actual Windows command preflight and MSVC compile
                      until GitHub Actions executes the new regression test.

GITHUB-ACTIONS-OBSERVED (b1r2, user log 115894793986):
WINDOWS-CI-OBSERVED:  6/7 tests passed. New Windows-only regression failed
                      at tests/test_builder.py line 73 before upstream build.
FAILED/BLOCKED:       b1r2 test incorrectly passed a quoted CALL command
                      via cmd.exe /c. Windows rejected the quote-wrapped script.
STATIC-VALIDATED:     b1r4 now tests actual VS2026/VS2022 developer-command
                      initialization through vswhere on Windows, instead of
                      relying on a fake developer environment.
NOT YET VERIFIED:     b1r4 actual Windows test and compiled launcher; hosted
                      Windows run is required before claiming those pass.
NOTE:                 The b1r2 log's synthetic "INDEPENDENT VALIDATED ZIP"
                      was a temporary unit-test fixture, NOT an application
                      release ZIP or evidence of packaging success.

STATIC-VALIDATED (b1r4): Synthetic unit fixture archive print is now
suppressed to avoid suggesting that a production app ZIP was created.


### b1r4 verification note
The b1r3 GitHub Actions run failed in `test_real_cmd_vscmd_spaced_path_and_missing_path` (fake developer environment returned 11). b1r4 replaces the mock-positive assertion with a Windows-hosted real Visual Studio toolchain test and improves diagnostic output. This change is not yet confirmed by Windows execution.
