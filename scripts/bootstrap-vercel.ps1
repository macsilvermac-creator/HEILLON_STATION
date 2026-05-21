<#
.SYNOPSIS
    Liga `frontend/` a um projeto Vercel, opcionalmente conecta o GitHub e define envs da API — sem login OAuth desde que exista VERCEL_TOKEN.

.PARAMETER VercelToken
    Personal Access Token (ou use $env:VERCEL_TOKEN).

.PARAMETER Team
    Slug ou ID do scope (opcional para conta Hobby quando é o primeiro projeto).

.PARAMETER ProjectName
    Nome do projeto na Vercel (criado se não existir com `link --yes`).

.PARAMETER GitRemoteUrl
    URL Git do remoto principal (HTTPS).

.PARAMETER BackendPublicUrl
    URL HTTPS pública da API FastAPI (ex.: Railway). Omitir para só fazer link + git connect sem env vars.

.NOTES
    Depois de correr este script confirme na Vercel: Settings → Root Directory → `frontend` (clone monorepo).
#>

param(
  [Parameter(Mandatory = $false)]
  [string] $VercelToken,

  [string] $Team = "",

  [Parameter(Mandatory = $true)]
  [string] $ProjectName,

  [string] $GitRemoteUrl = "https://github.com/macsilvermac-creator/HEILLON_STATION.git",

  [string] $BackendPublicUrl = ""
)

$ErrorActionPreference = "Stop"

if (-not $VercelToken -or $VercelToken.Trim().Length -eq 0) {
  $VercelToken = $env:VERCEL_TOKEN
}

if (-not $VercelToken -or $VercelToken.Trim().Length -eq 0) {
  Write-Error "Missing token: passe -VercelToken ou defina a variável de ambiente VERCEL_TOKEN."
  exit 1
}

$frontendPath = (Resolve-Path (Join-Path $PSScriptRoot "..\frontend")).ProviderPath
Push-Location $frontendPath

try {
  $scopeArgs = @()
  if ($Team -and $Team.Trim().Length -gt 0) {
    $scopeArgs = @("-S", $Team.Trim())
  }

  Write-Host ">> vercel link (projeto:" $ProjectName ")"
  if ($scopeArgs.Count -gt 0) {
    & npx --yes vercel@latest link --yes @scopeArgs --project $ProjectName -t $VercelToken
  }
  else {
    & npx --yes vercel@latest link --yes --project $ProjectName -t $VercelToken
  }

  if ($GitRemoteUrl.Trim().Length -gt 0) {
    Write-Host ">> vercel git connect" $GitRemoteUrl
    if ($scopeArgs.Count -gt 0) {
      & npx --yes vercel@latest git connect $GitRemoteUrl @scopeArgs -t $VercelToken
    }
    else {
      & npx --yes vercel@latest git connect $GitRemoteUrl -t $VercelToken
    }
  }

  $baseBackend = ""
  if (-not [string]::IsNullOrWhiteSpace($BackendPublicUrl)) {
    $baseBackend = $BackendPublicUrl.Trim().TrimEnd("/")
  }

  if ($baseBackend.Length -gt 0) {
    Write-Host ">> vercel env add BACKEND_PROXY_TARGET + INTERNAL_API_ORIGIN (production)"
    if ($scopeArgs.Count -gt 0) {
      & npx --yes vercel@latest env add BACKEND_PROXY_TARGET production --value $baseBackend --yes --no-sensitive @scopeArgs -t $VercelToken
      & npx --yes vercel@latest env add INTERNAL_API_ORIGIN production --value $baseBackend --yes --no-sensitive @scopeArgs -t $VercelToken
    }
    else {
      & npx --yes vercel@latest env add BACKEND_PROXY_TARGET production --value $baseBackend --yes --no-sensitive -t $VercelToken
      & npx --yes vercel@latest env add INTERNAL_API_ORIGIN production --value $baseBackend --yes --no-sensitive -t $VercelToken
    }

    Write-Host ""
    Write-Host "(Opcional) Repita para Preview se quiseres PRs funcionais:"
    Write-Host "  vercel env add BACKEND_PROXY_TARGET preview --value ... --yes --no-sensitive -t ..."
  }

  Write-Host ""
  Write-Host "IMPORTANTE — confirme no dashboard Vercel:"
  Write-Host "  Settings > General > Root Directory = frontend"
  Write-Host "  Backend FastAPI > CORS inclui https://*.vercel.app ou o seu domínio"
}
finally {
  Pop-Location
}
