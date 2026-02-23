param(
    [switch]$OneFile
)

$ErrorActionPreference = 'Stop'

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Split-Path -Parent $scriptDir
Set-Location $repoRoot

Write-Host 'Installing build dependencies...'
python -m pip install --upgrade pip
python -m pip install -e '.[build]'

$args = @(
    '--noconfirm',
    '--clean',
    '--windowed',
    '--name', 'Drevo',
    '--paths', 'src',
    '--collect-all', 'PySide6',
    'src/geneatree/__main__.py'
)

if ($OneFile) {
    $args += '--onefile'
}

Write-Host 'Building Windows executable...'
python -m PyInstaller @args

if ($OneFile) {
    Write-Host 'Done: dist\\Drevo.exe'
} else {
    Write-Host 'Done: dist\\Drevo\\Drevo.exe'
}
