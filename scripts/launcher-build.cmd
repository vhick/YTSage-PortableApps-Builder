@echo off
rem Reviewed, standalone build command template, not a launcher for end users.
rem All filenames arrive in Unicode environment variables from PowerShell.
call "%~dp0msvc_env.cmd"
if errorlevel 1 exit /b 11
rc.exe /nologo /fo"%YTS_RESOURCE%" "%YTS_RC%"
if errorlevel 1 exit /b 12
cl.exe /nologo /std:c++17 /EHsc /W4 /O2 /MT /DUNICODE /D_UNICODE "%YTS_SOURCE%" "%YTS_RESOURCE%" /link /SUBSYSTEM:WINDOWS /MACHINE:X64 /OUT:"%YTS_OUTPUT%" user32.lib shell32.lib
if errorlevel 1 exit /b 13
exit /b 0
