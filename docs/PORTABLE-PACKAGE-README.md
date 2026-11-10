YTSage Portable (Community) - unofficial PortableApps-style distribution
=======================================================================

PortableApps ZIP: extract the complete YTSagePortable folder to a writable drive.
Start YTSagePortable.exe at its root. Do not start App\YTSage\YTSage.exe
because that bypasses the portable environment. PortableApps Platform users
can refresh the menu. The installer is independently built with community NSIS,
NOT the official PortableApps.com installer and NOT a certified package.

Persistent data:
  Data\LocalAppData\YTSage\data\ytsage_config.json
  Data\LocalAppData\YTSage\data\ytsage_history.json
  Data\LocalAppData\YTSage\data\ytsage_download_queue.json
  Data\LocalAppData\YTSage\data\thumbnails\
  Data\LocalAppData\YTSage\logs\
  Data\LocalAppData\YTSage\bin\ (yt-dlp.exe, deno.exe)
  Data\DenoCache\
  Data\Downloads\ (initial default output folder)
  Data\TraceGuard\ (reserved; no unverified host harvesting is performed)

Data relocation: YTSage may store absolute download paths and cached helper
paths in JSON. Before moving the folder, finish downloads and close all children.
On another drive, check YTSage Settings > Download Location, then select the
new Data\Downloads folder. Other custom output locations remain user-controlled.

Upgrading: close YTSage; BACK UP THE ENTIRE YTSagePortable directory first.
Extract the new ZIP into a NEW adjacent folder. Copy the complete old Data
folder into the new one. Never overwrite/delete Data during upgrade.
If installing over an existing installation, confirm the installer preserves
Data and has no active YTSage processes. See runtime acceptance instructions.

Rollback: close the application. Restore the previous entire application
folder from backup, INCLUDING its matching Data snapshot. Later YTSage builds
can change JSON structures: mixing new data and old binaries isn't guaranteed.

Installed YTSage coexistence: no migration or cleanup of the installed profile
is attempted. The launcher modifies environment variables ONLY in its child
process tree. It will NOT change the system or user PATH. FFmpeg is bundled to
avoid the upstream FFmpeg installation routine that may execute setx PATH.

On first launch YTSage may download verified yt-dlp and Deno into Data.
Their network use, executable updates, browser cookie access when explicitly
selected, Windows file-history, AV scanning, temp files and Windows-managed
shell caches may create host activity. Do not claim zero host traces.

Neither code signing nor official PortableApps.com certification is claimed.
Download and use content only where you have rights and permission.
For support and licenses see Other\Source; app and packaging are not endorsed
by the upstream publisher.
