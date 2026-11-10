Builder kit b1r5 verification evidence (2026-11-10)
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


2026-11-10: b1r4 user GitHub Actions log logs_115903436647.zip
==========================================================
WINDOWS-COMPILED (b1r4): Seven actual Windows regression tests passed; Microsoft
                             Visual Studio 2026 MSVC launcher compiled correctly.
WINDOWS-CI-OBSERVED: Official v5.6.5 SHA-256 verified, tagged source checkout,
                     staging, and shared NSIS installer compilation succeeded.
FAILED/BLOCKED (b1r4): Independent installer validation erroneously expected
                        YTSagePortable/ archive folder; the shared NSIS builder
                        embeds .__UPB_Stage instead.
FAILED/BLOCKED (b1r4): The `validate.py zip` CLI did not run archive() with a
                        valid --dest due to a Python semicolon/if suite bug.
                        No work/out/*.zip was available for recovery or release.
STATIC-VALIDATED (b1r5): ZIP and inspect CLI paths corrected; end-to-end
                         synthetic fixtures added to validate disk outputs,
                         checksums, and reinspection. NSIS listing parser
                         verifies coherent launcher/App/Other payload paths.
NOT YET VERIFIED (b1r5): Windows hosted workflow, actual YTSage launch,
                          installed-app coexistence, installed NSIS execution,
                          Data preservation, publisher upload.

LOCAL b1r5 RESULTS (2026-11-10): 10 cross-platform regression tests PASSED;
                                Windows-only real MSVC regression SKIPPED
                                outside a Windows runner. Both workflows
                                parsed as YAML and all Python files compiled.
                                Real command-line ZIP and inspect operations
                                created and reverified a controlled test ZIP.
                                No released Windows application is claimed.
