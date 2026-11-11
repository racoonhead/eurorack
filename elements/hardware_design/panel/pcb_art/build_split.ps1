$ink = 'C:\Program Files\Inkscape\bin\inkscape.com'
Set-Location $PSScriptRoot

Write-Host ">>> Generating split panel vector layers..."
py gen_split_panels.py

$panels = @(
  @{ Dir = "split\exciter"; Prefix = "Exciter" },
  @{ Dir = "split\resonator"; Prefix = "Resonator" }
)

foreach ($p in $panels) {
  $d = $p.Dir
  $pfx = $p.Prefix
  Write-Host ">>> Converting text to paths for $pfx..."
  foreach ($name in @("${pfx}_F_SilkS", "${pfx}_F_Silver_Cu_Mask", "${pfx}_preview")) {
    $src = "$d\$name.svg"
    $tmp = "$d\$name.tmp.svg"
    & $ink $src --export-text-to-path --export-plain-svg --export-type=svg --export-filename=$tmp 2>$null
    Move-Item $tmp $src -Force
  }
  & $ink "$d\${pfx}_preview.svg" --export-type=png --export-width=2000 --export-filename="$d\${pfx}_preview.png" 2>$null
}

Write-Host ">>> Rendering composite side-by-side rack preview..."
& $ink "split\split_panels_preview.svg" --export-type=png --export-width=3200 --export-filename="split\split_panels_preview.png" 2>$null

Write-Host ">>> Done!"

