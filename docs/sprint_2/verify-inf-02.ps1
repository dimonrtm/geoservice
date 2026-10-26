$ErrorActionPreference = 'Stop'
& node (Join-Path $PSScriptRoot 'inf-02/run.mjs')
exit $LASTEXITCODE
