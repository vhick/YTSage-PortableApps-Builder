YTSage PORTABLEAPPS - Windows acceptance tests (manual; do NOT mark passed by CI)
=============================================================================
Run these on a disposable Windows 10/11 x64 VM using Process Monitor where useful.
Have both installed YTSage and an ordinary test account available. Disable
network only in tests explicitly marked offline. Work on disposable files.

A. Launch and UI
1. Extract the release ZIP to C:\Portable Test\YTSagePortable.
2. Launch the root YTSagePortable.exe, check main window, menus, About, URL
   arguments, video analysis (permitted source), yt-dlp/Deno setup and FFmpeg.
3. Verify ffmpeg.exe and ffprobe.exe are used from App\YTSage. Verify neither
   HKCU User PATH nor machine PATH changed. Confirm the first-run setup did not
   execute setx.exe; investigate if it did. Capture real ProcMon output.
4. Verify `Data\LocalAppData\YTSage\data` contains config and that `bin`,
   `logs`, thumbnails, history, queue and nested empty folders persist.
5. Close the GUI; wait for any active yt-dlp/FFmpeg/Deno child. Confirm the
   launcher exits and download files are neither truncated nor lost.
6. Start again, check settings, window geometry, history, queue and outputs.
7. Test Unicode and spaces, new user, read-only drive (graceful error), URL
   arguments, removable drive letter change, and nested long path (document limit).

B. Host protection and coexistence
8. Before starting, snapshot user %LOCALAPPDATA%\YTSage and HKCU user PATH,
   and add pre-existing files plus nested empty folders (in a test account).
9. Run portable YTSage, download samples, change settings, then fully exit.
   Existing installed YTSage data/paths must be unchanged. Also test with
   installed YTSage running and report conflicts.
10. Check APPDATA, LocalLow, ProgramData, shell shortcuts, registry, Jump Lists,
    Windows Notifications and TEMP with before/after ProcMon. Attribute writes
    to YTSage, Qt, yt-dlp, FFmpeg, Deno, installer and Windows separately.
11. Do NOT automatically remove or harvest any host state. If actual app-owned
    writable paths are found, assess a bounded launcher/data patch in a new
    reviewed kit revision. Preserve pre-existing/changed files and empty trees.
12. Confirm no startup entry, scheduled task, service, registry file protocol,
    uninstall record or shell shortcut is created by the ZIP-only launch.
    Check installer-only changes BEFORE the first application launch.
13. If Windows notifications exist, test action and click-to-open; note which
    shell caches remain. This PySide6 app is NOT assumed to use Electron CLSIDs.

C. Upgrade, crash, installer
14. Start a download; terminate just the launcher and verify application child
    remains or document exact behavior. Kill app process in disposable VM and
    restart, checking queue/config corruption and recoverability.
15. Copy package to a different drive; verify startup and manually reset
    absolute custom output folder/cached helper paths if required.
16. Extract newer package to fresh folder and copy entire old Data. Test first
    launch, settings and downloaded tools. Test rollback with matching snapshot.
17. On a disposable VM, run .paf.exe interactively, inspect install destination,
    reinstall, upgrade and preservation of all Data/empty directories. Confirm
    no user's installed profile/shortcuts are touched and no system PATH change.
18. Test selected file from USB drive, PortalApps Platform menu refresh,
    extraction from ZIP, and root launcher execution without admin rights.
19. Record tested package filename, SHA256, Windows build, disk path, launcher
    runtime, traces, installer behavior, test outcome, and associated log.

CI only validates code structure, hash/signature, ZIP files, launcher compilation,
installer PE/archive structure. It cannot prove these interactive tests passed.
