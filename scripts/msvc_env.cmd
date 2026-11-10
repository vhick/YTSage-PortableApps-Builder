@echo off
rem Called from launcher-build.cmd. Must not setlocal: the MSVC environment
rem must remain available to rc.exe and cl.exe in the same cmd process.
if not defined YTS_DEV_CMD (
  >&2 echo ERROR: YTS_DEV_CMD was not provided by build_launcher.ps1.
  exit /b 31
)
if not exist "%YTS_DEV_CMD%" (
  >&2 echo ERROR: VsDevCmd.bat was not found at the verified path.
  exit /b 32
)
call "%YTS_DEV_CMD%" -arch=amd64 -host_arch=amd64 >nul
if errorlevel 1 (
  >&2 echo ERROR: Visual Studio developer environment initialization failed.
  exit /b 11
)
exit /b 0
