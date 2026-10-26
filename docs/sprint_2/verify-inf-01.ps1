param([ValidateRange(10, 300)][int] $TimeoutSeconds = 60)

$ErrorActionPreference = 'Stop'
$repoRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$project = 'geoservice-inf01-' + [guid]::NewGuid().ToString('N').Substring(0, 12)
$probeNames = @("$project-api", "$project-negative", "$project-demo-settings")
$tempRoot = Join-Path ([IO.Path]::GetTempPath()) $project
$savedEnvironment = @{}
$exitCode = 0
$cookieError = 'AUTH_SESSION_COOKIE_SECURE должно быть true, если DEV_MODE=false'

function Invoke-Docker {
    param([string[]] $Arguments, [int] $LimitSeconds = 30, [switch] $AllowFailure)
    $info = [Diagnostics.ProcessStartInfo]::new('docker')
    $info.UseShellExecute = $false
    $info.CreateNoWindow = $true
    $info.RedirectStandardOutput = $true
    $info.RedirectStandardError = $true
    $info.StandardOutputEncoding = [Text.Encoding]::UTF8
    $info.StandardErrorEncoding = [Text.Encoding]::UTF8
    foreach ($argument in $Arguments) { $info.ArgumentList.Add($argument) }
    $process = [Diagnostics.Process]::new()
    $process.StartInfo = $info
    try {
        [void] $process.Start()
        $stdout = $process.StandardOutput.ReadToEndAsync()
        $stderr = $process.StandardError.ReadToEndAsync()
        if (-not $process.WaitForExit($LimitSeconds * 1000)) {
            $process.Kill($true)
            $process.WaitForExit()
            throw "Docker: превышено ожидание $LimitSeconds секунд."
        }
        $result = [pscustomobject]@{
            Code = $process.ExitCode
            Out = $stdout.GetAwaiter().GetResult().Trim()
            Err = $stderr.GetAwaiter().GetResult().Trim()
        }
        if ($result.Code -ne 0 -and -not $AllowFailure) {
            # Не раскрывать environment, токены или build output в диагностике.
            $diagnostic = $result.Err -replace 'synthetic-[A-Za-z0-9-]+', '[test-value]' -replace 'postgresql\+asyncpg://\S+', '[test-db-url]'
            if ($diagnostic.Length -gt 1500) { $diagnostic = $diagnostic.Substring($diagnostic.Length - 1500) }
            throw "Docker $($Arguments[0]): exit=$($result.Code). $diagnostic"
        }
        return $result
    }
    finally { $process.Dispose() }
}

function Assert-Probe([bool] $Condition, [string] $Message) {
    if (-not $Condition) { throw $Message }
}

function Get-ProbeState([string] $Name) {
    $state = Invoke-Docker -Arguments @('inspect', '--format', '{{json .State}}', $Name)
    return $state.Out | ConvertFrom-Json
}

try {
    Write-Output "Project: $project"
    Write-Output (Invoke-Docker -Arguments @('version', '--format', '{{.Client.Version}} / {{.Server.Version}}')).Out
    Write-Output (Invoke-Docker -Arguments @('compose', 'version', '--short')).Out
    [void] [IO.Directory]::CreateDirectory($tempRoot)
    $basePath = Join-Path $repoRoot 'infra/docker-compose.yml'
    $demoPath = Join-Path $repoRoot 'infra/docker-compose.demo.yml'
    $yaml = [IO.File]::ReadAllText($basePath) + [IO.File]::ReadAllText($demoPath)
    $variableNames = @([regex]::Matches($yaml, '\$\{([A-Za-z_][A-Za-z0-9_]*)') | ForEach-Object { $_.Groups[1].Value })
    $variableNames += @(Get-ChildItem Env: | Where-Object { $_.Name -like 'COMPOSE_*' -or $_.Name -like 'AUTH_SESSION_*' } | ForEach-Object Name)
    $variableNames += 'DEV_MODE'
    foreach ($name in ($variableNames | Sort-Object -Unique)) {
        $savedEnvironment[$name] = [Environment]::GetEnvironmentVariable($name, 'Process')
        Remove-Item -LiteralPath "Env:$name" -ErrorAction SilentlyContinue
    }
    $envPath = Join-Path $tempRoot 'probe.env'
    [IO.File]::WriteAllText($envPath, "DB_NAME=inf01_unused`nDB_USER=probe`nDB_PASSWORD=synthetic-probe-password`nDATABASE_URL=postgresql+asyncpg://probe:probe@127.0.0.1:1/inf01_unused`nJWT_SECRET=synthetic-inf01-probe-secret`n", [Text.UTF8Encoding]::new($false))
    $compose = @('compose', '--project-name', $project, '--env-file', $envPath, '-f', $basePath)
    $baseConfig = (Invoke-Docker -Arguments ($compose + @('config', '--format', 'json'))).Out | ConvertFrom-Json -AsHashtable
    $demoConfig = (Invoke-Docker -Arguments ($compose + @('-f', $demoPath, 'config', '--format', 'json'))).Out | ConvertFrom-Json -AsHashtable
    $base = $baseConfig.services.utility_service
    $demo = $demoConfig.services.utility_service
    Assert-Probe ($base.build.target -eq 'prod' -and ($base.command -join ' ') -eq 'bash -lc bash scripts/start_api.sh') 'Base target/command не соответствует контракту.'
    Write-Output 'Сборка production API (лимит 10 минут)...'
    $null = Invoke-Docker -Arguments ($compose + @('build', 'utility_service')) -LimitSeconds 600
    $null = Invoke-Docker -Arguments ($compose + @('run', '--no-deps', '-d', '--name', $probeNames[0], 'utility_service'))
    $imageId = (Invoke-Docker -Arguments @('inspect', '--format', '{{.Image}}', $probeNames[0])).Out
    Write-Output "Prod image: $imageId"

    $healthCode = 'import json,urllib.request; r=urllib.request.urlopen("http://127.0.0.1:8000/health",timeout=2); assert r.status==200; assert json.load(r)=={"ok":True}'
    $deadline = [DateTime]::UtcNow.AddSeconds($TimeoutSeconds)
    $healthy = $false
    do {
        $state = Get-ProbeState $probeNames[0]
        if (-not $state.Running) {
            $logs = Invoke-Docker -Arguments @('logs', '--tail', '60', $probeNames[0])
            if (($logs.Out + $logs.Err).Contains($cookieError)) { throw "Base startup: $cookieError" }
            throw "Base API завершился до готовности: exit=$($state.ExitCode)."
        }
        $health = Invoke-Docker -Arguments @('exec', $probeNames[0], 'python', '-c', $healthCode) -LimitSeconds 5 -AllowFailure
        if ($health.Code -eq 0) { $healthy = $true; break }
        Start-Sleep -Milliseconds 250
    } while ([DateTime]::UtcNow -lt $deadline)
    Assert-Probe $healthy 'Base API не ответил на /health в пределах таймаута.'
    Assert-Probe ($base.environment.DEV_MODE -eq 'false' -and $base.environment.AUTH_SESSION_COOKIE_SECURE -eq 'true') 'Base environment не соответствует production-политике.'
    $null = Invoke-Docker -Arguments @('exec', $probeNames[0], 'python', '-c', 'from utility_service.utils.settings import settings; assert settings.dev_auth_enabled is False; assert settings.auth_session_cookie_secure is True')
    Write-Output 'PASS: base startup, HTTP 200 /health, runtime DEV_MODE=false / Secure=true.'

    $null = Invoke-Docker -Arguments ($compose + @('run', '--no-deps', '-d', '--name', $probeNames[1], '-e', 'AUTH_SESSION_COOKIE_SECURE=false', 'utility_service'))
    $deadline = [DateTime]::UtcNow.AddSeconds($TimeoutSeconds)
    do {
        $state = Get-ProbeState $probeNames[1]
        if (-not $state.Running) { break }
        Start-Sleep -Milliseconds 250
    } while ([DateTime]::UtcNow -lt $deadline)
    Assert-Probe (-not $state.Running -and $state.ExitCode -ne 0) 'Небезопасный production запуск не завершился ожидаемым отказом.'
    $logs = Invoke-Docker -Arguments @('logs', '--tail', '60', $probeNames[1])
    Assert-Probe (($logs.Out + $logs.Err).Contains($cookieError)) 'Negative startup завершился по другой причине.'
    Write-Output 'PASS: Secure=false отклонён production-валидатором.'

    Assert-Probe ($demo.environment.DEV_MODE -eq 'true' -and $demo.environment.AUTH_SESSION_COOKIE_SECURE -eq 'false') 'Demo merged environment не соответствует HTTP demo.'
    Assert-Probe ($demo.build.target -eq 'dev' -and ($demo.command -join ' ') -eq 'bash -lc bash scripts/start_utility_service.sh') 'Demo target/command изменился.'
    $demoEnvPath = Join-Path $tempRoot 'demo-resolved.env'
    $demoLines = @($demo.environment.GetEnumerator() | Sort-Object Key | ForEach-Object {
        Assert-Probe (-not ([string]$_.Value).Contains("`n") -and -not ([string]$_.Value).Contains("`r")) 'Многострочный environment не поддерживается проверкой.'
        '{0}={1}' -f $_.Key, $_.Value
    })
    [IO.File]::WriteAllText($demoEnvPath, ($demoLines -join "`n") + "`n", [Text.UTF8Encoding]::new($false))
    $null = Invoke-Docker -Arguments @('run', '--name', $probeNames[2], '--label', "com.docker.compose.project=$project", '--network', 'none', '--read-only', '-e', 'PYTHONDONTWRITEBYTECODE=1', '--env-file', $demoEnvPath, '--entrypoint', 'python', $imageId, '-c', 'from utility_service.utils.settings import settings; assert settings.dev_auth_enabled is True; assert settings.auth_session_cookie_secure is False')
    Write-Output 'PASS: demo merge и Settings; БД и demo seeds не запускались.'
}
catch {
    $exitCode = 1
    Write-Output "FAIL: $($_.Exception.Message)"
}
finally {
    try {
        $containers = Invoke-Docker -Arguments @('ps', '-aq', '--filter', "label=com.docker.compose.project=$project")
        foreach ($id in ($containers.Out -split '\r?\n' | Where-Object { $_ })) {
            $item = @((Invoke-Docker -Arguments @('inspect', $id)).Out | ConvertFrom-Json)[0]
            Assert-Probe ($item.Config.Labels.'com.docker.compose.project' -eq $project -and $item.Name.TrimStart('/') -in $probeNames) 'Cleanup: ресурс не принадлежит проверке.'
            $null = Invoke-Docker -Arguments @('rm', '-f', $id)
        }
        $networks = Invoke-Docker -Arguments @('network', 'ls', '-q', '--filter', "label=com.docker.compose.project=$project")
        foreach ($id in ($networks.Out -split '\r?\n' | Where-Object { $_ })) {
            $item = @((Invoke-Docker -Arguments @('network', 'inspect', $id)).Out | ConvertFrom-Json)[0]
            Assert-Probe ($item.Labels.'com.docker.compose.project' -eq $project -and $item.Name -eq "${project}_default") 'Cleanup: неожиданная сеть.'
            $null = Invoke-Docker -Arguments @('network', 'rm', $id)
        }
        Write-Output 'PASS: cleanup контейнеров и сети проверки.'
    }
    catch { $exitCode = 1; Write-Output "FAIL cleanup: $($_.Exception.Message)" }
    foreach ($name in $savedEnvironment.Keys) {
        if ($null -eq $savedEnvironment[$name]) {
            Remove-Item -LiteralPath "Env:$name" -ErrorAction SilentlyContinue
        }
        else { [Environment]::SetEnvironmentVariable($name, $savedEnvironment[$name], 'Process') }
    }
    # Только два известных временных файла; без рекурсивного удаления.
    try {
        foreach ($filename in @('probe.env', 'demo-resolved.env')) {
            $path = Join-Path $tempRoot $filename
            if ([IO.File]::Exists($path)) { [IO.File]::Delete($path) }
        }
        if ([IO.Directory]::Exists($tempRoot)) { [IO.Directory]::Delete($tempRoot) }
    }
    catch { $exitCode = 1; Write-Output 'FAIL cleanup: не удалось удалить временные файлы проверки.' }
}
exit $exitCode
