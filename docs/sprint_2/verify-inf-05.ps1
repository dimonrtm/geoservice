$ErrorActionPreference = 'Stop'
& node (Join-Path $PSScriptRoot 'inf-05/run.mjs') @args
exit $LASTEXITCODE
