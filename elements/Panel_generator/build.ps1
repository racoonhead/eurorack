$ErrorActionPreference = "Stop"
$dir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $dir

$python = "C:\Program Files\KiCad\10.0\bin\python.exe"

Write-Host "1/2 Building Category Showcase (LIGHT / AUDIO / VIDEO) & Key_frames Panel..."
& $python gen_showcase.py

Write-Host "Done!"

