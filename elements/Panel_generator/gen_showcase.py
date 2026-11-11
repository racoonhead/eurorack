#!/usr/bin/env python3
"""
Generates a side-by-side visual comparison (category_comparison.png) of the 3
DECØY DEVICES module categories using the exact same unified panel architecture
while differentiating 6 coordinated visual elements:
  1. AUDIO (Synth / DSP)   — Matte BLACK PCB (#0c0c0e) + White Silk + Silver Copper
  2. LIGHT (DMX / Stage)   — Matte WHITE PCB (#f2f2ee) + Black Silk + Silver Copper
  3. VIDEO (RGB / Sync)    — Cyber PURPLE PCB (#190d2e) + White Silk + Silver Copper
"""
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from panel_sdk import FONT, PanelCanvas, chamfer_rect, circle, dashed_line, diamond, line, poly, rect, text
from gen_keyframes import build_keyframes_panel

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
INKSCAPE_BIN = r"C:\Program Files\Inkscape\bin\inkscape.com"


def build_demo_module(category, title, subtitle, sys_code, serial_left, serial_right):
    """Builds a 20HP representative panel for each category sharing the exact same layout grid."""
    p = PanelCanvas(hp=20, category=category)
    W = p.w
    p.add_mounting_holes()
    p.add_header(title=title, subtitle=subtitle, sys_code=sys_code, title_size=4.65)

    # Top row of 4 Standard Pots + Labels + LEDs (unified grid across all 3 categories)
    X_POTS = [14.0, 38.47, 62.93, 87.4]
    pot_lbls = {
        "AUDIO": ["FREQ", "RESO", "MORPH", "DAMP"],
        "LIGHT": ["PAN", "TILT", "DIMMER", "STROBE"],
        "VIDEO": ["H-POS", "V-POS", "CONTRAST", "SOLAR"],
    }[category]

    for i, cx in enumerate(X_POTS):
        p.silk.append(line(cx - 2.0, 11.2, cx + 2.0, 11.2, w=0.18))
        p.silk.append(line(cx, 10.7, cx, 11.7, w=0.18))
        p.pot_scale(cx, 22.0, r_hole=3.75, style="standard")
        p.silk.append(text(cx, 32.2, pot_lbls[i], size=2.0, weight="700", spacing=0.22))
        tick_in = max(4.0, len(pot_lbls[i]) * 0.78 + 0.8)
        p.silver.append(line(cx - tick_in - 1.4, 31.5, cx - tick_in, 31.5, w=0.22))
        p.silver.append(line(cx + tick_in, 31.5, cx + tick_in + 1.4, 31.5, w=0.22))
        p.led_indicator(cx, 36.8, r_hole=1.6)

    # Middle Section: Left Mode Button + Key LED, Center Big Pot + Wing Emblem, Right Attenuverter
    p.silver.append(poly([(3.5, 44.0), (6.0, 42.5), (36.5, 42.5)], w=0.22, close=False))
    p.silver.append(poly([(W - 3.5, 44.0), (W - 6.0, 42.5), (64.9, 42.5)], w=0.22, close=False))
    p.silk.append(circle(36.5, 42.5, 0.35, fill=True))
    p.silk.append(circle(64.9, 42.5, 0.35, fill=True))

    Y_MID = 58.0
    # Left button + LED
    p.holes.append((16.5, Y_MID, 2.65, "BTN"))
    p.silver.append(circle(16.5, Y_MID, 3.55, w=0.25))
    p.silk.append(circle(16.5, Y_MID, 4.15, w=0.32))
    btn_lbl = {"AUDIO": "MODEL", "LIGHT": "SCENE", "VIDEO": "SYNC"}[category]
    p.silk.append(text(16.5, Y_MID + 6.5, btn_lbl, size=1.95, weight="700", spacing=0.28))

    p.led_indicator(31.0, Y_MID, r_hole=1.6)
    p.silver.append(line(21.0, Y_MID, 28.0, Y_MID, w=0.25))
    p.silver.append(line(34.0, Y_MID, 50.7 - 14.8, Y_MID, w=0.25))

    # Center Big Potentiometer (with category-specific central HUD wings!)
    p.pot_scale(50.7, Y_MID, r_hole=3.75, style="big", skip_top=False)
    main_lbl = {"AUDIO": "TIMBRE", "LIGHT": "MASTER", "VIDEO": "LUMA"}[category]
    p.silk.append(chamfer_rect(50.7, 70.5, 18.5, 3.8, c=1.0, w=0.32))
    p.silk.append(text(50.7, 71.35, main_lbl, size=2.30, weight="700", spacing=0.35))
    p.silver.append(line(50.7 - 12.8, 70.5, 50.7 - 9.8, 70.5, w=0.30))
    p.silver.append(line(50.7 + 9.8, 70.5, 50.7 + 12.8, 70.5, w=0.30))

    # Right Medium Potentiometer
    p.pot_scale(84.5, Y_MID, r_hole=3.75, style="medium")
    p.silver.append(line(84.5 - 4.8, Y_MID + 6.8, 84.5 - 3.4, Y_MID + 6.8, w=0.28))
    p.silver.append(line(84.5 + 3.4, Y_MID + 6.8, 84.5 + 4.8, Y_MID + 6.8, w=0.28))
    p.silver.append(line(84.5 + 4.1, Y_MID + 6.1, 84.5 + 4.1, Y_MID + 7.5, w=0.28))
    p.silk.append(text(84.5, 69.2, "MODULATION", size=1.95, weight="700", spacing=0.22))
    p.silver.append(line(50.7 + 14.8, Y_MID, 84.5 - 8.2, Y_MID, w=0.25))

    # Bottom Section: 2x5 Jack Matrix (Inputs on top row, Outputs on bottom row)
    p.silver.append(line(3.5, 78.5, 34.0, 78.5, w=0.30))
    p.silver.append(line(67.4, 78.5, W - 3.5, 78.5, w=0.30))
    p.silk.append(line(3.5, 78.5, 3.5, 80.3, w=0.30))
    p.silk.append(line(W - 3.5, 78.5, W - 3.5, 80.3, w=0.30))
    sec_lbl = {
        "AUDIO": "CV MODULATION // AUDIO I/O",
        "LIGHT": "CV INPUTS // DMX SCENE OUTPUTS",
        "VIDEO": "SYNC & CV IN // RGB VIDEO OUT",
    }[category]
    p.silk.append(text(50.7, 79.1, sec_lbl, size=1.60, weight="600", spacing=0.22))

    X_JACKS = [14.2, 32.45, 50.7, 68.95, 87.2]
    in_lbls = {
        "AUDIO": ["V/OCT", "FM IN", "RESO CV", "MORPH CV", "STRIKE"],
        "LIGHT": ["SCENE CV", "PAN CV", "TILT CV", "DIM CV", "STROBE"],
        "VIDEO": ["H-SYNC", "V-SYNC", "LUMA IN", "KEY CV", "SOLAR CV"],
    }[category]
    out_lbls = {
        "AUDIO": ["AUX", "RAW", "SUB", "MAIN L", "MAIN R"],
        "LIGHT": ["STEP", "OUT 1", "OUT 2", "OUT 3", "OUT 4"],
        "VIDEO": ["SYNC OUT", "LUMA", "RED", "GREEN", "BLUE"],
    }[category]

    for i, jx in enumerate(X_JACKS):
        # Top Row: Inputs
        p.jack_graphic(jx, 88.5, r_hole=3.2, is_output=False)
        p.silk.append(text(jx, 96.6, in_lbls[i], size=1.85, weight="700", spacing=0.18))
        p.silver.append(line(jx - 4.5, 97.4, jx + 4.5, 97.4, w=0.18))

        # Bottom Row: Outputs (in chamfered frames)
        p.jack_graphic(jx, 107.0, r_hole=3.2, is_output=True)
        p.silver.append(chamfer_rect(jx, 114.8, 14.2, 3.2, c=0.8, w=0.28))
        p.silver.append(text(jx, 115.55, out_lbls[i], size=1.85, weight="700", spacing=0.20))

    p.add_footer(serial_left=serial_left, serial_right=serial_right)
    return p


def generate_comparison_sheet():
    p_audio = build_demo_module("AUDIO", "EXCITER", "MODAL SYNTH // V0.4", "DSP.32", "DD-AU01 // REV 0.4", "EXC-01-STM32")
    p_light = build_demo_module("LIGHT", "LUX_BEAM", "DMX SCENE CTRL // V0.1", "8CH.DAC", "DD-LX01 // REV 0.1", "LUX-01-STM32")
    p_video = build_demo_module("VIDEO", "RASTER", "RGB SYNC CORE // V0.2", "RGB.1V", "DD-VD01 // REV 0.2", "RST-01-FPGA")

    margin = 8.0
    gap = 8.0
    header_h = 20.0
    pw = p_audio.w
    ph = p_audio.h

    total_w = margin * 2 + pw * 3 + gap * 2
    total_h = margin * 2 + header_h + ph

    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{total_w:.2f}mm" height="{total_h:.2f}mm" viewBox="0 0 {total_w:.2f} {total_h:.2f}">',
        f'  <rect x="0" y="0" width="{total_w:.2f}" height="{total_h:.2f}" fill="#16171c"/>'
    ]

    titles = [
        (
            "1. AUDIO MODULES (AUD // BLACK PCB)",
            "Matte Black Mask • Wave Badge • Radial Scales • Circular Jacks • Hazard Stripes",
            "#b9bec7"
        ),
        (
            "2. LIGHT MODULES (LUX // WHITE PCB)",
            "Matte White Mask • Beam Badge • Photometric Dot Scales • Octagonal Jacks • Prism Chevrons",
            "#f2f2ee"
        ),
        (
            "3. VIDEO MODULES (VID // PURPLE PCB)",
            "Cyber Purple Mask • CRT Badge • T-Graticule Scales • Viewfinder Jacks • SMPTE Sync Bar",
            "#c39ef8"
        ),
    ]

    for idx, (panel, (t_main, t_sub, col)) in enumerate(zip([p_audio, p_light, p_video], titles)):
        x0 = margin + idx * (pw + gap)
        y0 = margin + header_h
        cx = x0 + pw / 2
        svg.append(f'  <text x="{cx:.2f}" y="{margin + 7.0:.2f}" font-family="{FONT}" font-weight="700" font-stretch="semi-condensed" font-size="3.8" fill="#f4f4f0" text-anchor="middle" letter-spacing="0.35">{t_main}</text>')
        svg.append(f'  <text x="{cx:.2f}" y="{margin + 12.8:.2f}" font-family="{FONT}" font-weight="600" font-stretch="semi-condensed" font-size="2.15" fill="{col}" text-anchor="middle" letter-spacing="0.15">{t_sub}</text>')
        svg.append("  " + panel.render_preview_group(x0, y0))

    svg.append("</svg>")
    svg_path = os.path.join(OUT_DIR, "category_comparison.svg")
    png_path = os.path.join(OUT_DIR, "category_comparison.png")
    with open(svg_path, "w", encoding="utf-8") as f:
        f.write("\n".join(svg))

    if os.path.exists(INKSCAPE_BIN):
        subprocess.run([
            INKSCAPE_BIN, svg_path,
            "--export-text-to-path",
            "--export-plain-svg",
            f"--export-filename={svg_path}"
        ], check=True)
        subprocess.run([
            INKSCAPE_BIN, svg_path,
            "--export-type=png",
            "--export-dpi=220",
            f"--export-filename={png_path}"
        ], check=True)
    print(f"Saved showcase comparison: {png_path}")


if __name__ == "__main__":
    generate_comparison_sheet()
    # Also rebuild Key_frames in its default LIGHT category (White PCB + LIGHT HUD pattern)
    kf_out = os.path.abspath(os.path.join(OUT_DIR, "..", "Key_frames", "hardware_design", "panel", "pcb_art"))
    panel = build_keyframes_panel(category="LIGHT")
    panel.export_all(kf_out)
