$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $PSScriptRoot
$issPath = Join-Path $PSScriptRoot 'ScriptsFormula.iss'

$innoCandidates = @(
    'C:\Program Files (x86)\Inno Setup 6\ISCC.exe',
    'C:\Program Files\Inno Setup 6\ISCC.exe'
)

$iscc = $null
foreach ($candidate in $innoCandidates) {
    if (Test-Path $candidate) {
        $iscc = $candidate
        break
    }
}

if (-not $iscc) {
    Write-Host 'Inno Setup nao encontrado.' -ForegroundColor Red
    Write-Host 'Instale em: https://jrsoftware.org/isdl.php' -ForegroundColor Yellow
    exit 1
}

Write-Host "Compilando instalador Scripts Formula..." -ForegroundColor Cyan
Push-Location $repoRoot
& $iscc $issPath
Pop-Location

if ($LASTEXITCODE -ne 0) {
    Write-Host 'Falha na compilacao do instalador.' -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host 'Instalador gerado em dist/Scripts-Formula-Setup.exe' -ForegroundColor Green
