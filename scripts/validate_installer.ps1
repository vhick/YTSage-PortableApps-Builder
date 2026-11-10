param([Parameter(Mandatory)][string]$Path,[Parameter(Mandatory)][string]$Sha256)
$ErrorActionPreference='Stop'
$actual=(Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
if ($actual -ne $Sha256.ToLowerInvariant()) {throw 'Installer SHA256 mismatch'}
if (-not $Path.EndsWith('.paf.exe',[StringComparison]::OrdinalIgnoreCase)) {throw 'Wrong installer extension'}
$f=[IO.File]::OpenRead($Path)
try {
  $r=[IO.BinaryReader]::new($f)
  if ($r.ReadUInt16() -ne 0x5a4d) {throw 'Missing MZ header'}
  $f.Position=0x3c
  $offset=$r.ReadInt32()
  if($offset -lt 64 -or $offset -ge $f.Length-4) {throw 'Invalid PE offset'}
  $f.Position=$offset
  if($r.ReadUInt32() -ne 0x4550) {throw 'Missing PE signature'}
} finally {$f.Dispose()}
$seven = Get-Command 7z.exe -ErrorAction SilentlyContinue
if (-not $seven) {$seven = Get-Command 7za.exe -ErrorAction SilentlyContinue}
if (-not $seven) {throw '7-Zip command required for NSIS archive validation'}
& $seven.Source t -bso0 -bsp0 $Path | Out-Host
if($LASTEXITCODE -ne 0) {throw 'Installer archive test failed'}
$list = & $seven.Source l -slt $Path
if($LASTEXITCODE -ne 0) {throw 'Installer listing failed'}
if(-not (($list -join "`n") -match 'YTSagePortable(?:\\|/)')) {throw 'Installer does not appear to contain portable app root'}
Write-Host "VALIDATED installer binary/archive: $Path SHA256=$actual (execution not tested in headless CI)"
