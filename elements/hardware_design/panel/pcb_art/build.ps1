# Rebuild all PCB art: py gen_panel.py, then convert text to outlines so fonts are not needed by the fab / KiCad.
$ink = 'C:\Program Files\Inkscape\bin\inkscape.com'
Set-Location $PSScriptRoot
py gen_panel.py
foreach ($n in 'F_SilkS','F_Silver_Cu_Mask','preview') {
  & $ink "$n.svg" --export-text-to-path --export-plain-svg --export-type=svg --export-filename="$n.tmp.svg" 2>$null
  Move-Item "$n.tmp.svg" "$n.svg" -Force
}
& $ink preview.svg --export-type=png --export-width=3000 --export-filename=preview.png 2>$null
