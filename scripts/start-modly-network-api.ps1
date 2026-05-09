param(
  [string]$HostName = "0.0.0.0",
  [int]$Port = 8765,
  [string]$Token = $env:MODLY_API_TOKEN,
  [string]$CorsOrigins = "*",
  [string]$ModelsDir = $env:MODELS_DIR,
  [string]$WorkspaceDir = $env:WORKSPACE_DIR,
  [string]$ExtensionsDir = $env:EXTENSIONS_DIR
)

$ErrorActionPreference = "Stop"

$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$ApiDir = Join-Path $RepoRoot "api"
$DataDir = Join-Path $RepoRoot "data"
$VenvPython = Join-Path $ApiDir ".venv\Scripts\python.exe"
$Python = if (Test-Path $VenvPython) { $VenvPython } else { "python" }

if (-not $Token) {
  Write-Warning "MODLY_API_TOKEN is not set and -Token was not provided. The Modly API will start without auth."
}

if (-not $ModelsDir) { $ModelsDir = Join-Path $DataDir "models" }
if (-not $WorkspaceDir) { $WorkspaceDir = Join-Path $DataDir "workspace" }
if (-not $ExtensionsDir) { $ExtensionsDir = Join-Path $DataDir "extensions" }

New-Item -ItemType Directory -Force -Path $ModelsDir, $WorkspaceDir, $ExtensionsDir | Out-Null

$argsList = @(
  (Join-Path $ApiDir "serve.py"),
  "--host", $HostName,
  "--port", "$Port",
  "--cors-origins", $CorsOrigins,
  "--models-dir", $ModelsDir,
  "--workspace-dir", $WorkspaceDir,
  "--extensions-dir", $ExtensionsDir
)

if ($Token) {
  $argsList += @("--token", $Token)
}

Push-Location $ApiDir
try {
  & $Python @argsList
} finally {
  Pop-Location
}
