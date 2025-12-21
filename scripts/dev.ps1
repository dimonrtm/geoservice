param(
  [Parameter(Mandatory=$true)]
  [ValidateSet("check","precommit","ci","format")]
  [string]$Task
)

$ErrorActionPreference = "Stop"

function Write-Info($msg) {
  Write-Host ""
  Write-Host "==> $msg"
}

function Run($cmd, $cwd = $null) {
  Write-Host $cmd
  if ($cwd) { Push-Location $cwd }
  try { iex $cmd }
  finally { if ($cwd) { Pop-Location } }
}

function CmdExists($name) {
  return $null -ne (Get-Command $name -ErrorAction SilentlyContinue)
}

function FindCondaEnvPython() {
  $candidates = @(
    (Join-Path $env:USERPROFILE "anaconda3\envs\geoservice-dev\python.exe"),
    (Join-Path $env:USERPROFILE "miniconda3\envs\geoservice-dev\python.exe"),
    "C:\ProgramData\Anaconda3\envs\geoservice-dev\python.exe",
    "C:\ProgramData\Miniconda3\envs\geoservice-dev\python.exe",
    "C:\Users\dimon\anaconda3\envs\geoservice-dev\python.exe"
  )

  foreach ($p in $candidates) {
    if ($p -and (Test-Path $p)) { return $p }
  }
  return $null
}

function RunPreCommit() {
  # 1) If pre-commit is available directly, use it
  if (CmdExists "pre-commit") {
    Run "pre-commit run --all-files"
    return
  }

  # 2) If we can find env python.exe, run pre-commit as a module (most reliable for conda env)
  $envPy = FindCondaEnvPython
  if ($envPy) {
    Write-Info "pre-commit not found in PATH. Using env python: $envPy"
    & $envPy -m pre_commit run --all-files
    if ($LASTEXITCODE -ne 0) { throw "pre-commit failed (exit code $LASTEXITCODE)" }
    return
  }

  # 3) Fallback: if conda exists in PATH, try conda run
  if (CmdExists "conda") {
    Write-Info "pre-commit not found in PATH. Trying: conda run -n geoservice-dev pre-commit ..."
    Run "conda run -n geoservice-dev pre-commit run --all-files"
    return
  }

  throw "pre-commit not found. Activate conda env 'geoservice-dev' OR ensure its python.exe exists under anaconda3\envs\geoservice-dev."
}

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $RepoRoot

if ($Task -in @("check","precommit","ci")) {
  Write-Info "Running pre-commit"
  RunPreCommit
}

if ($Task -in @("check","ci","format")) {
  # Optional frontend
  if (Test-Path (Join-Path $RepoRoot "frontend\package.json")) {
    Write-Info "Frontend detected"
    if (Test-Path (Join-Path $RepoRoot "frontend\package-lock.json")) {
      Run "npm ci" (Join-Path $RepoRoot "frontend")
    } else {
      Run "npm install" (Join-Path $RepoRoot "frontend")
    }
  } else {
    Write-Info "No frontend/package.json, skipping frontend steps"
  }

  # Optional backend
  $backend = Join-Path $RepoRoot "backend"
  if (Test-Path $backend) {
    $sln = Get-ChildItem -Path $backend -Recurse -Filter *.sln -ErrorAction SilentlyContinue | Select-Object -First 1
    $csproj = Get-ChildItem -Path $backend -Recurse -Filter *.csproj -ErrorAction SilentlyContinue | Select-Object -First 1

    if ($sln -or $csproj) {
      $target = if ($sln) { $sln.FullName } else { $csproj.FullName }
      Write-Info "Backend detected: running dotnet format verify"
      Run "dotnet format `"$target`" --verify-no-changes"
    } else {
      Write-Info "No .sln/.csproj under backend/, skipping dotnet steps"
    }
  } else {
    Write-Info "No backend/, skipping dotnet steps"
  }
}

Write-Info "Done"
