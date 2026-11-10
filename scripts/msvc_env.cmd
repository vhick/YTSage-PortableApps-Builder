@echo off
rem This script runs in the SAME cmd process as rc.exe/cl.exe.
rem Do not SETLOCAL: the genuine VsDevCmd.bat environment must persist.
if not defined YTS_DEV_CMD (
  >&2 echo ERROR: YTS_DEV_CMD was not provided by build_launcher.ps1.
  exit /b 31
)
if not exist "%YTS_DEV_CMD%" (
  >&2 echo ERROR: VsDevCmd.bat does not exist at the detected path: "%YTS_DEV_CMD%"
  exit /b 32
)
rem Do not hide stdout here. When Visual Studio initialization fails,
rem the original tool diagnostics are essential for debugging.
call "%YTS_DEV_CMD%" -arch=amd64 -host_arch=amd64
if errorlevel 1 (
  >&2 echo ERROR: VsDevCmd.bat returned a nonzero status: %ERRORLEVEL%.
  exit /b 11
)
rem The compiler and resource tools must be available to the SAME cmd.exe.
where.exe cl.exe >nul 2>nul
if errorlevel 1 (
  >&2 echo ERROR: cl.exe missing from PATH after VsDevCmd.bat.
  exit /b 41
)
where.exe rc.exe >nul 2>nul
if errorlevel 1 (
  >&2 echo ERROR: rc.exe missing from PATH after VsDevCmd.bat.
  exit /b 42
)
exit /b 0
