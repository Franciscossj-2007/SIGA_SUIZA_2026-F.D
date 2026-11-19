[CmdletBinding()]
param(
    [string]$ProjectName = 'siga-suiza-2026',
    [string]$CustomDomain = '',
    [string]$ApiUrl = ''
)

$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $PSScriptRoot
$LinkFile = Join-Path $Root '.vercel\project.json'

function Invoke-Vercel {
    param(
        [Parameter(ValueFromRemainingArguments = $true)]
        [string[]]$VercelArgs
    )
    $previous = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try {
        & npx --yes vercel@latest @VercelArgs
    } finally {
        $ErrorActionPreference = $previous
    }
}

if (-not (Test-Path -LiteralPath $LinkFile)) {
    throw "No se encontro '$LinkFile'. Ejecuta el script desde el clone del repositorio con el proyecto Vercel original linkeado."
}

$originalLink = Get-Content -LiteralPath $LinkFile -Raw
$link = $originalLink | ConvertFrom-Json
$scope = $link.orgId

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  SIGA - NUEVA VISTA (CLON) PARA LA COMPANERA              " -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Proyecto actual : $($link.projectName)" -ForegroundColor Gray
Write-Host "Nuevo proyecto  : $ProjectName" -ForegroundColor Green
Write-Host "Dominio esperado: https://$ProjectName.vercel.app" -ForegroundColor Green
Write-Host "Team scope      : $scope" -ForegroundColor Gray

if (-not (Get-Command npx -ErrorAction SilentlyContinue)) {
    throw "Se requiere npx (Node.js) para ejecutar la CLI de Vercel."
}

Push-Location $Root
try {
    Write-Host "`n[1/6] Verificando sesion de Vercel..." -ForegroundColor Blue
    $who = Invoke-Vercel whoami
    if ($LASTEXITCODE -ne 0) {
        throw "No hay sesion activa en Vercel. Ejecuta 'vercel login' y vuelve a intentar. Salida: $who"
    }
    Write-Host "      -> Autenticado como: $who" -ForegroundColor Green

    $viteVars = @{}
    Write-Host "`n[2/6] Leyendo variables VITE_* del proyecto actual ($($link.projectName))..." -ForegroundColor Blue
    $tmpEnv = Join-Path $env:TEMP "siga-vercel-env-$([guid]::NewGuid().ToString('N')).env"
    try {
        Invoke-Vercel env pull $tmpEnv --environment production --yes | Out-Host
        if ($LASTEXITCODE -ne 0) { throw "No se pudieron leer las variables de entorno del proyecto actual." }
        foreach ($line in (Get-Content -LiteralPath $tmpEnv)) {
            if ($line -match '^\s*(?:export\s+)?(VITE_[A-Za-z0-9_]*)\s*=\s*(.*)$') {
                $viteVars[$matches[1]] = $matches[2].Trim().Trim('"').Trim("'")
            }
        }
    } finally {
        if (Test-Path -LiteralPath $tmpEnv) { Remove-Item -LiteralPath $tmpEnv -Force }
    }

    if ($ApiUrl) { $viteVars['VITE_API_URL'] = $ApiUrl }

    if (-not $viteVars.ContainsKey('VITE_API_URL') -or -not $viteVars['VITE_API_URL']) {
        throw "No se encontro VITE_API_URL en el proyecto actual. Pasa el valor con -ApiUrl 'https://...'"
    }

    foreach ($key in ($viteVars.Keys | Sort-Object)) {
        Write-Host "      -> $key configurada" -ForegroundColor Green
    }

    Write-Host "`n[3/6] Creando proyecto '$ProjectName' (si ya existe se reutiliza)..." -ForegroundColor Blue
    Invoke-Vercel project create $ProjectName --scope $scope | Out-Host
    if ($LASTEXITCODE -ne 0) {
        Write-Host "      -> El proyecto ya existe o no se pudo crear; se continua con el existente." -ForegroundColor Yellow
    }

    Write-Host "`n[4/6] Linkeando el repositorio al nuevo proyecto..." -ForegroundColor Blue
    Invoke-Vercel link --yes --project $ProjectName --scope $scope | Out-Host
    if ($LASTEXITCODE -ne 0) { throw "No se pudo linkear el nuevo proyecto." }

    Write-Host "`n[5/6] Copiando variables VITE_* a los 3 entornos..." -ForegroundColor Blue
    foreach ($key in ($viteVars.Keys | Sort-Object)) {
        foreach ($target in @('production', 'preview', 'development')) {
            Invoke-Vercel env add $key --environment $target --value $viteVars[$key] --no-sensitive --force --yes | Out-Host
            if ($LASTEXITCODE -ne 0) { throw "Fallo al configurar $key en $target." }
        }
        Write-Host "      -> $key OK (production, preview, development)" -ForegroundColor Green
    }

    Write-Host "`n[6/6] Desplegando a produccion..." -ForegroundColor Blue
    $deployOutput = Invoke-Vercel deploy --prod --yes
    $deployOutput | Out-Host
    if ($LASTEXITCODE -ne 0) { throw "Fallo el deploy de produccion." }

    $prodUrl = "https://$ProjectName.vercel.app"
    $aliasLine = $deployOutput | Where-Object { $_ -match 'Aliased\s+https://' } | Select-Object -Last 1
    if ($aliasLine -and $aliasLine -match 'https://[^\s]+') {
        $prodUrl = $matches[0]
    }

    Write-Host "`nConectando repositorio GitHub (rama main)..." -ForegroundColor Blue
    Invoke-Vercel git connect -p $ProjectName --yes | Out-Host
    if ($LASTEXITCODE -ne 0) {
        Write-Host "      -> No se pudo conectar Git; hazlo desde Settings > Git en Vercel." -ForegroundColor Yellow
    }

    if ($CustomDomain) {
        Write-Host "`nConfigurando dominio propio '$CustomDomain'..." -ForegroundColor Blue
        Invoke-Vercel domains add $CustomDomain $ProjectName --scope $scope | Out-Host
        if ($LASTEXITCODE -ne 0) { Write-Host "Revisa el dominio manualmente en Vercel." -ForegroundColor Yellow }
        Write-Host "Verificar DNS luego: vercel domains verify $CustomDomain --project $ProjectName" -ForegroundColor Yellow
    }

    Write-Host "`n============================================================" -ForegroundColor Cyan
    Write-Host " LISTO. Misma DB/backend de Railway, otro proyecto y dominio." -ForegroundColor Green
    Write-Host " URL: $prodUrl" -ForegroundColor Green
    if ($CustomDomain) { Write-Host " URL custom: https://$CustomDomain" -ForegroundColor Green }
    Write-Host " ============================================================" -ForegroundColor Cyan
} finally {
    Pop-Location
    [System.IO.File]::WriteAllText($LinkFile, $originalLink)
    Write-Host "`nLink original restaurado a '$($link.projectName)'." -ForegroundColor Gray
}
