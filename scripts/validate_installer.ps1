param([Parameter(Mandatory)][string]$Path, [Parameter(Mandatory)][string]$Sha256)
$ErrorActionPreference = 'Stop'
# Python is already a required, pinned environment in both GitHub workflows.
$helper = Join-Path $PSScriptRoot 'validate_installer.py'
if (-not (Test-Path -LiteralPath $helper -PathType Leaf)) {
    throw "Missing installer validator: $helper"
}
& python $helper --path $Path --sha256 $Sha256
if ($LASTEXITCODE -ne 0) {
    throw "Independent installer verification failed (exit $LASTEXITCODE)"
}
