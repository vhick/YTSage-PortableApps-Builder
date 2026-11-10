param([Parameter(Mandatory)][string]$Stage)
$ErrorActionPreference='Stop'
$root = (Resolve-Path "$PSScriptRoot/..").Path
$stage = (Resolve-Path -LiteralPath $Stage).Path
$ico = Join-Path $stage 'App/AppInfo/appicon.ico'
if (-not (Test-Path -LiteralPath $ico)) { throw 'Authentic upstream icon must be staged first' }
$vswhere = "${env:ProgramFiles(x86)}\Microsoft Visual Studio\Installer\vswhere.exe"
if (-not (Test-Path -LiteralPath $vswhere)) { throw 'Missing VS vswhere executable' }
$vsdir = & $vswhere -latest -products '*' -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
if ($LASTEXITCODE -ne 0 -or -not $vsdir) { throw 'VS C++ tools missing' }
$devcmd = Join-Path $vsdir 'Common7/Tools/VsDevCmd.bat'
if (-not (Test-Path -LiteralPath $devcmd)) { throw 'Missing VS devcmd' }
$src = Join-Path $root 'launcher/YTSagePortable.cpp'
$out = Join-Path $stage 'YTSagePortable.exe'
$rc = Join-Path $stage 'portable-icon.rc'
$res = Join-Path $stage 'portable-icon.res'
# Keep RC content ASCII and paths Unicode-safe: icon is relative to this RC file.
[IO.File]::WriteAllText($rc, "101 ICON `"App/AppInfo/appicon.ico`"`r`n", [Text.Encoding]::ASCII)
# The command runner is a committed ASCII .cmd script rather than dynamic batch
# text assembled from PowerShell array expressions. This avoids the b1r1 bug
# that split the quoted VsDevCmd path into three separate batch commands.
# Carry paths through Unicode Windows environment variables; the cmd syntax
# itself contains no localized/non-ASCII path strings.
$env:YTS_DEV_CMD = $devcmd
$env:YTS_SOURCE = $src
$env:YTS_OUTPUT = $out
$env:YTS_RESOURCE = $res
$env:YTS_RC = $rc
$batch = Join-Path $root 'scripts/launcher-build.cmd'
if (-not (Test-Path -LiteralPath $batch)) { throw 'Missing reviewed launcher-build.cmd' }
Push-Location $stage
try {
  & $batch
  $exitCode = $LASTEXITCODE
  if ($exitCode -ne 0) { throw "MSVC launcher compilation failed: $exitCode" }
} finally {
  Pop-Location
  Remove-Item -LiteralPath $rc,$res -ErrorAction SilentlyContinue
  Get-ChildItem -LiteralPath $stage -File | Where-Object { $_.Extension -in @('.obj','.ilk','.pdb','.exp','.lib') } | Remove-Item -Force
}
if (-not (Test-Path -LiteralPath $out)) { throw 'Compiled root executable not produced' }
Write-Host "COMPILED YTSagePortable.exe: $out"
