$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '../../../..')).Path
$network = 'geoservice-body-probe-' + [guid]::NewGuid().ToString('N').Substring(0, 10)
$api = $network + '-api'
$proxy = $network + '-proxy'
$backendImage = 'geoservice-day14-check:latest'
$frontendImage = 'geoservice-inf02-e06a7579-frontend-prod:latest'
$probe = '/evidence/nginx_body_limit_probe.py'
function Invoke-Docker {
    & docker @args
    if ($LASTEXITCODE -ne 0) { throw "Docker failed: $($args[0])" }
}
try {
    Invoke-Docker network create --internal $network
    Invoke-Docker run -d --name $api --network $network --network-alias utility_service --read-only --tmpfs /tmp -e PYTHONDONTWRITEBYTECODE=1 --mount "type=bind,source=$repoRoot/apps/backend,target=/app,readonly" --mount "type=bind,source=$PSScriptRoot,target=/evidence,readonly" -w /app --entrypoint python $backendImage $probe server
    Invoke-Docker run -d --name $proxy --network $network --network-alias proxy --mount "type=bind,source=$repoRoot/apps/frontend/nginx.conf,target=/etc/nginx/conf.d/default.conf,readonly" $frontendImage
    Invoke-Docker exec $proxy nginx -v
    $result = Invoke-Docker run --rm --network $network --read-only --tmpfs /tmp -e PYTHONDONTWRITEBYTECODE=1 --mount "type=bind,source=$repoRoot/apps/backend,target=/app,readonly" --mount "type=bind,source=$PSScriptRoot,target=/evidence,readonly" -w /app --entrypoint python $backendImage $probe client
    $result | Write-Output
    [IO.File]::WriteAllText((Join-Path $PSScriptRoot 'nginx-body-limit-result.json'), (($result -join "`n") + "`n"), [Text.UTF8Encoding]::new($false))
} finally {
    & docker rm -f $proxy $api
    & docker network rm $network
    if ($LASTEXITCODE -ne 0) { throw 'Probe network cleanup failed' }
}
