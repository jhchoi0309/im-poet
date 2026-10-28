# Optional PowerShell launcher; direct Python commands work without changing execution policy.
$ErrorActionPreference = 'Stop'
foreach ($name in @('py', 'python3', 'python')) {
    $candidate = Get-Command $name -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($null -eq $candidate) { continue }
    $prefix = @()
    if ($name -eq 'py') { $prefix = @('-3') }
    & $candidate.Source @prefix -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)' 2>$null
    if ($LASTEXITCODE -eq 0) {
        & $candidate.Source @prefix (Join-Path $PSScriptRoot 'install.py') @args
        exit $LASTEXITCODE
    }
}
Write-Error 'Python 3.10 or newer is required. Try installing Python from python.org.'
exit 1
