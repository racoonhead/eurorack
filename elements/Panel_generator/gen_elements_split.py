#!/usr/bin/env python3
"""
DECØY DEVICES — Elements v0.4 Dual-Tone Split Front Panel Generator
Powered by Panel_generator / panel_sdk.py

Architecture:
  - Total width: 34 HP (172.5 mm total)
  - EXCITER section:   20 HP (101.4 x 128.5 mm) -> Matte Black PCB + White Silk + Silver HASL
  - RESONATOR section: 14 HP ( 70.9 x 128.5 mm) -> Matte White PCB + Black Silk + Silver HASL
  - Mounting holes: ONLY 4 outer holes (2 far left on Exciter, 2 far right on Resonator).
                    NO inner rack holes — panels are clamped together by motherboard pots & jacks!
  - Switch 1 (Exciter): 2 models (1: Classic, 2: Industrial Metal/Burst/Samples)
  - Switch 2 (Resonator): 8 models (1-3 Original, 4-7 Rings, 8: Kammerl Spectral Clouds)
"""
import math
import os
import re
import sys
import subprocess

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from panel_sdk import (
    PanelCanvas, line, dashed_line, circle, arc, poly, chamfer_rect, octagon, diamond, text, rect, FONT
)

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(HERE, ".."))
OUT_DIR = os.path.join(HERE, "output_elements")
PCB_ART_SPLIT = os.path.join(REPO_ROOT, "hardware_design", "panel", "pcb_art", "split")

W_EXC = 101.4   # 20 HP
W_RES = 70.9    # 14 HP
H_PANEL = 128.5
PX = 0.12321

def draw_elements_big_pot(canvas, cx, cy, r_hole=3.75):
    """Clean cyberpunk scale for Elements big knobs (FLOW, MALLET, GEOMETRY, BRIGHTNESS).
    Guarantees zero overlap with labels below (lowest point at y = cy + 5.7mm max)."""
    canvas.holes.append((cx, cy, r_hole, "POT"))
    # Inner silver ring
    canvas.silver.append(circle(cx, cy, 6.2, w=0.25))

    # 23 radial ticks spanning 244 degrees (-122 to +122 deg from 12 o'clock / polar 148 to 392 deg)
    n_ticks = 23
    for i in range(n_ticks):
        deg = 148.0 + i * (244.0 / (n_ticks - 1))
        rad = math.radians(deg)
        is_major = (i % 2 == 0)
        is_mid = (i == 11)  # 270 deg (top)
        r1 = 7.6
        r2 = 9.1 if is_major else 8.5
        w = 0.28 if (is_major or is_mid) else 0.18
        x1 = cx + r1 * math.cos(rad)
        y1 = cy + r1 * math.sin(rad)
        x2 = cx + r2 * math.cos(rad)
        y2 = cy + r2 * math.sin(rad)
        canvas.silk.append(line(x1, y1, x2, y2, w=w))

    # Outer silver arc with end dots at 148 and 392 deg
    canvas.silver.append(arc(cx, cy, 9.9, 148, 392, w=0.25))
    for deg in (148.0, 392.0):
        rad = math.radians(deg)
        dot_x = cx + 9.9 * math.cos(rad)
        dot_y = cy + 9.9 * math.sin(rad)
        canvas.silver.append(circle(dot_x, dot_y, 0.45, fill=True))

def build_split_panels():
    # -------------------------------------------------------------------------
    # 1. BUILD EXCITER PANEL (20 HP, BLACK MASK, WHITE SILK, SILVER FINISH)
    # -------------------------------------------------------------------------
    exc = PanelCanvas(hp=20, category="AUDIO", mask="black", finish="silver")
    exc.w = W_EXC
    exc.h = H_PANEL

    # ONLY 2 outer mounting holes on far-left (NO inner holes!)
    exc.holes.append((7.49, 2.99, 1.6, "MOUNT"))
    exc.holes.append((7.49, 125.51, 1.6, "MOUNT"))
    exc.silver.append(circle(7.49, 2.99, 2.60, w=0.22))
    exc.silver.append(circle(7.49, 125.51, 2.60, w=0.22))

    # Header with AUDIO Oscilloscope badge
    exc.draw_category_badge(14.8, 4.0)
    exc.silk.append(text(18.8, 5.8, "ELEMENTS", size=4.75, anchor="start", weight="700", spacing=0.55))
    exc.silver.append(line(18.8, 1.3, 58.5, 1.3, w=0.22))
    exc.silver.append(line(36.0, 6.85, 59.5, 6.85, w=0.18))
    exc.silver.append(text(61.5, 3.45, "EXCITER SECTION // 20HP", size=1.75, anchor="start", weight="600", spacing=0.15))
    bx = 61.5
    for bw in [1.4, 0.5, 0.9, 2.0, 0.5, 0.5, 1.3, 0.6, 1.6]:
        exc.silk.append(rect(bx, 4.45, bw, 1.35, fill=True))
        bx += bw + 0.50
    exc.silver.append(text(76.2, 5.65, "AUD.EXC.02", size=1.35, anchor="start", weight="600", spacing=0.14))

    # Header divider line (double silver line + >>> chevrons on right)
    exc.silver.append(line(3.0, 8.2, W_EXC - 3.0, 8.2, w=0.40))
    exc.silk.append(line(3.0, 8.2, 3.0, 10.6, w=0.30))
    exc.silk.append(line(3.0, 9.8, 5.2, 9.8, w=0.25))
    exc.silver.append(line(3.0, 9.0, W_EXC - 3.0, 9.0, w=0.15))
    for i in range(4):
        ax = W_EXC - 10.5 + i * 1.5
        exc.silk.append(poly([(ax, 8.4), (ax + 0.8, 9.0), (ax, 9.6)], w=0.25, close=False))

    # Pots scales (Top row) - pot_scale automatically appends 3.75mm hole
    top_pots_exc = [16.73, 40.51, 64.32, 88.17]
    for cx in top_pots_exc:
        exc.pot_scale(cx, 21.23, r_hole=3.75, style="standard")

    # Connect top pots (CONTOUR -> BOW -> BLOW -> STRIKE)
    for a, b in zip(top_pots_exc[:3], top_pots_exc[1:4]):
        exc.silver.append(dashed_line(a + 8.5, 21.23, b - 8.5, 21.23, w=0.25, dash="0.8,0.8"))

    # Top labels + Industrial Mode 2 sub-labels
    # CONTOUR
    exc.silk.append(text(16.73, 31.6, "CONTOUR", size=2.65, weight="700", spacing=0.25))
    for dx_, kindname in ((-8.8, "sharp"), (8.8, "round")):
        ix, iy = 16.73 + dx_ * 1.09, 29.2
        exc.silk.append(circle(ix, iy, 1.5, w=0.18))
        if kindname == "sharp":
            exc.silk.append(poly([(ix - .8, iy + .6), (ix + .5, iy - .7), (ix + .5, iy + .6)], w=0.18, close=False))
        else:
            exc.silk.append(f'<path d="M {ix-.85:.3f} {iy+.55:.3f} C {ix-.85:.3f} {iy-.95:.3f} {ix+.85:.3f} {iy-.95:.3f} {ix+.85:.3f} {iy+.55:.3f}" fill="none" stroke="CURR" stroke-width="0.18"/>')

    # BOW: Friction (metal on metal)
    exc.silk.append(text(40.51, 31.6, "BOW", size=2.65, weight="700", spacing=0.25))
    exc.silver.append(text(40.51, 34.2, "[ FRICTION ]", size=1.25, weight="600", spacing=0.15))

    # BLOW: Digital Burst (silver chamfer frame)
    exc.silver.append(chamfer_rect(64.32, 31.6 - 0.7, 13.5, 3.8, c=1.0, w=0.25))
    exc.silver.append(text(64.32, 31.6, "BLOW", size=2.65, weight="700", spacing=0.25))
    exc.silver.append(text(64.32, 34.2, "[ BURST ]", size=1.25, weight="600", spacing=0.15))

    # STRIKE: Industrial Samples (white silk chamfer frame)
    exc.silk.append(chamfer_rect(88.17, 31.6 - 0.7, 14.8, 3.8, c=1.0, w=0.22))
    exc.silk.append(text(88.17, 31.6, "STRIKE", size=2.65, weight="700", spacing=0.25))
    exc.silver.append(text(88.17, 34.2, "[ SAMPLES ]", size=1.25, weight="600", spacing=0.15))

    # Big Knobs: FLOW & MALLET (using tailored scale with zero overlap with labels)
    draw_elements_big_pot(exc, 47.81, 48.39, r_hole=3.75)
    draw_elements_big_pot(exc, 80.83, 48.39, r_hole=3.75)
    exc.silver.append(chamfer_rect(47.81, 57.2, 13.8, 3.4, c=0.8, w=0.25))
    exc.silver.append(text(47.81, 57.7, "FLOW", size=2.50, weight="700", spacing=0.25))
    exc.silk.append(chamfer_rect(80.83, 57.2, 16.0, 3.4, c=0.8, w=0.22))
    exc.silk.append(text(80.83, 57.7, "MALLET", size=2.50, weight="700", spacing=0.25))

    # PLAY Button (manually append 5.1mm hole)
    exc.holes.append((16.73, 43.77, 5.1, "PLAY"))
    exc.silver.append(circle(16.73, 43.77, 7.0, w=0.30))
    for i in range(36):
        a = math.radians(360 * i / 36)
        exc.silk.append(line(16.73 + 8.2 * math.sin(a), 43.77 - 8.2 * math.cos(a), 16.73 + 9.2 * math.sin(a), 43.77 - 9.2 * math.cos(a), w=0.20))
    exc.silk.append(text(28.0, 44.5, "PLAY", size=2.65, anchor="start", weight="700", spacing=0.25))

    # Switch 1: Exciter Model Switch (x=76.31, y=63.21) + LED (x=64.32, y=57.74)
    exc.led_indicator(64.32, 57.74, r_hole=2.52)
    exc.holes.append((76.31, 63.21, 2.55, "BTN"))
    exc.silk.append(circle(76.31, 63.21, 3.65, w=0.22))
    exc.silk.append(text(76.31, 69.8, "MODEL", size=2.10, weight="700", spacing=0.25))
    # Arrow from button toward LED
    exc.silver.append(poly([(71.5, 62.2), (70.3, 63.21), (71.5, 64.2)], w=0.28, close=False))

    # Mid row: TIMBRE pots (x=40.51, 64.32, 88.17, y=75.52)
    for cx in (40.51, 64.32, 88.17):
        exc.pot_scale(cx, 75.52, r_hole=3.75, style="medium")
    exc.silk.append(text(40.51, 86.0, "TIMBRE", size=2.65, weight="700", spacing=0.25))
    exc.silver.append(chamfer_rect(64.32, 86.0 - 0.7, 16.0, 3.8, c=1.0, w=0.25))
    exc.silver.append(text(64.32, 86.0, "TIMBRE", size=2.65, weight="700", spacing=0.25))
    exc.silk.append(chamfer_rect(88.17, 86.0 - 0.7, 16.0, 3.8, c=1.0, w=0.22))
    exc.silk.append(text(88.17, 86.0, "TIMBRE", size=2.65, weight="700", spacing=0.25))

    # Left column jacks (8 jacks) — perfectly balanced vertical clearances
    left_jacks = [
        (10.70, 64.41, "V/OCT", "A", 57.0),
        (22.76, 64.41, "FM", "A", 57.0),
        (10.70, 79.97, "GATE", "A", 72.7),
        (22.76, 79.97, "STRENGTH", "A", 72.7),
        (10.70, 95.53, "EXT IN", "B", 87.75),
        (22.76, 95.53, "EXT IN", "C", 87.75),
        (10.70, 111.08, "OUT L", "OUT", None),
        (22.76, 111.08, "OUT R", "OUT", None),
    ]
    for jx, jy, jlbl, jstyle, y_lbl in left_jacks:
        is_out = (jstyle == "OUT")
        exc.jack_graphic(jx, jy, r_hole=3.25, is_output=is_out)
        if jstyle == "A":
            exc.silk.append(text(jx, y_lbl, jlbl, size=2.10, weight="700", spacing=0.20))
        elif jstyle == "B":
            exc.silver.append(chamfer_rect(jx, y_lbl, 13.0, 3.2, c=0.8, w=0.22))
            exc.silver.append(text(jx, y_lbl + 0.65, jlbl, size=1.85, weight="700", spacing=0.15))
        elif jstyle == "C":
            exc.silk.append(chamfer_rect(jx, y_lbl, 13.0, 3.2, c=0.8, w=0.20))
            exc.silk.append(text(jx, y_lbl + 0.65, jlbl, size=1.85, weight="700", spacing=0.15))

    # OUT L / OUT R silver surround box
    for ox, onm in ((10.70, "OUT L"), (22.76, "OUT R")):
        exc.silver.append(chamfer_rect(ox, 109.4, 10.6, 16.4, c=1.6, w=0.30))
        exc.silk.append(text(ox, 104.3, onm, size=2.20, weight="700", spacing=0.25))

    # Attenuverter columns (5 columns = 10 jacks)
    att_x = [38.32, 51.34, 64.32, 77.34, 90.32]
    for ax in att_x:
        exc.jack_graphic(ax, 95.53, r_hole=3.25, is_output=False)
        exc.jack_graphic(ax, 111.08, r_hole=3.25, is_output=False)
        # Attenuverter polarity indicator − | +
        exc.silk.append(line(ax - 3.9, 90.5, ax - 2.5, 90.5, w=0.18))
        exc.silk.append(line(ax + 2.5, 90.5, ax + 3.9, 90.5, w=0.18))
        exc.silk.append(line(ax + 3.2, 89.8, ax + 3.2, 91.2, w=0.18))
        exc.silk.append(line(ax, 89.4, ax, 91.4, w=0.18))
        exc.silver.append(dashed_line(ax, 95.53 + 3.25 + 1.8, ax, 111.08 - 3.25 - 1.8, w=0.28, dash="0.8,0.8"))

    # Signal routing lines (FLOW and MALLET to attenuverters)
    exc.silver.append(dashed_line(47.81, 59.9, 47.81, 89.0, w=0.28, dash="0.8,0.8"))
    exc.silver.append(circle(47.81, 59.9, 0.50, fill=True))
    exc.silver.append(circle(47.81, 89.0, 0.50, fill=True))

    pts_mallet = [(80.83, 59.9), (80.83, 70.5), (77.34, 74.5), (77.34, 89.0)]
    for (x1, y1), (x2, y2) in zip(pts_mallet, pts_mallet[1:]):
        exc.silver.append(dashed_line(x1, y1, x2, y2, w=0.28, dash="0.8,0.8"))
    exc.silver.append(circle(80.83, 59.9, 0.50, fill=True))
    exc.silver.append(circle(77.34, 89.0, 0.50, fill=True))

    # Right edge interface / bus connector (mates with Resonator)
    exc.silver.append(line(W_EXC - 2.8, 13.0, W_EXC - 2.8, 114.0, w=0.25))
    for py_node in (25.0, 48.0, 75.0, 95.0, 111.0):
        exc.silver.append(poly([(W_EXC - 2.8, py_node - 1.2), (W_EXC - 1.2, py_node), (W_EXC - 2.8, py_node + 1.2)], fill=True))
        exc.silver.append(circle(W_EXC - 4.9, py_node, 0.60, fill=True))
        exc.silver.append(line(W_EXC - 4.9, py_node, W_EXC - 2.8, py_node, w=0.22))

    # Footer
    exc.add_footer(serial_left="DD-EL04-EXC // 20HP", serial_right="EXC.02", brand="DECØY DEVICES")

    # -------------------------------------------------------------------------
    # 2. BUILD RESONATOR PANEL (14 HP, WHITE MASK, BLACK SILK, SILVER FINISH)
    # -------------------------------------------------------------------------
    res = PanelCanvas(hp=14, category="AUDIO", mask="white", finish="silver")
    res.w = W_RES
    res.h = H_PANEL

    # ONLY 2 outer mounting holes on far-right (NO inner holes!)
    res.holes.append((W_RES - 7.33, 2.99, 1.6, "MOUNT"))
    res.holes.append((W_RES - 7.33, 125.51, 1.6, "MOUNT"))
    res.silver.append(circle(W_RES - 7.33, 2.99, 2.60, w=0.22))
    res.silver.append(circle(W_RES - 7.33, 125.51, 2.60, w=0.22))

    # Header with AUDIO Oscilloscope badge (compacted for 14 HP to clear top-right mount hole)
    res.draw_category_badge(8.5, 4.0)
    res.silk.append(text(12.2, 5.8, "RESONATOR", size=3.85, anchor="start", weight="700", spacing=0.40))
    res.silver.append(line(12.2, 1.3, 38.0, 1.3, w=0.22))
    res.silver.append(line(26.0, 6.85, 38.0, 6.85, w=0.18))
    res.silver.append(text(39.5, 3.45, "8-MODELS // 14HP", size=1.55, anchor="start", weight="600", spacing=0.15))
    bx = 39.5
    for bw in [1.2, 0.4, 0.8, 1.6, 0.4, 0.4, 1.0]:
        res.silk.append(rect(bx, 4.45, bw, 1.35, fill=True))
        bx += bw + 0.45
    res.silver.append(text(48.0, 5.65, "AUD.RES.08", size=1.25, anchor="start", weight="600", spacing=0.14))

    # Header divider line (ends at x = W_RES - 10.5 mm to avoid top-right mounting hole circle)
    res.silver.append(line(3.0, 8.2, W_RES - 10.5, 8.2, w=0.40))
    res.silver.append(line(3.0, 9.0, W_RES - 10.5, 9.0, w=0.15))
    for i in range(3):
        ax = W_RES - 16.0 + i * 1.5
        res.silk.append(poly([(ax, 8.4), (ax + 0.8, 9.0), (ax, 9.6)], w=0.25, close=False))

    # Top Pots (COARSE, FINE, FM) - pot_scale automatically appends 3.75mm hole
    top_pots_res = [111.98 - W_EXC, 135.79 - W_EXC, 159.61 - W_EXC]
    for cx in top_pots_res:
        res.pot_scale(cx, 21.23, r_hole=3.75, style="standard")

    res.silk.append(text(top_pots_res[0], 31.6, "COARSE", size=2.65, weight="700", spacing=0.25))
    res.silk.append(text(top_pots_res[1], 31.6, "FINE", size=2.65, weight="700", spacing=0.25))
    res.silk.append(text(top_pots_res[2], 31.6, "FM", size=2.65, weight="700", spacing=0.25))
    # FM polarity icons
    fmx = top_pots_res[2]
    for dx_, sym in ((-8.8, "-"), (8.8, "+")):
        ix, iy = fmx + dx_ * 1.09, 29.2
        res.silk.append(circle(ix, iy, 1.5, w=0.18))
        res.silk.append(line(ix - .7, iy, ix + .7, iy, w=0.18))
        if sym == "+":
            res.silk.append(line(ix, iy - .7, ix, iy + .7, w=0.18))

    # Big Knobs: GEOMETRY & BRIGHTNESS (using tailored scale with zero overlap with labels)
    draw_elements_big_pot(res, 119.28 - W_EXC, 48.39, r_hole=3.75)
    draw_elements_big_pot(res, 152.30 - W_EXC, 48.39, r_hole=3.75)
    res.silk.append(text(119.28 - W_EXC, 57.6, "GEOMETRY", size=2.45, weight="700", spacing=0.22))
    res.silk.append(text(152.30 - W_EXC, 57.6, "BRIGHTNESS", size=2.40, weight="700", spacing=0.18))

    # Switch 2: Resonator Model Switch (local x = 22.50, y = 63.21) + LED (local x = 34.39, y = 57.74)
    res.led_indicator(34.39, 57.74, r_hole=2.52)
    res.holes.append((22.50, 63.21, 2.55, "BTN"))
    res.silk.append(circle(22.50, 63.21, 3.65, w=0.22))
    res.silk.append(text(22.50, 69.8, "MODEL", size=2.10, weight="700", spacing=0.25))
    # Arrow from button toward LED
    res.silver.append(poly([(27.3, 62.2), (28.5, 63.21), (27.3, 64.2)], w=0.28, close=False))

    # Mid row: DAMPING, POSITION, SPACE (3 pots)
    mid_pots_res = [111.98 - W_EXC, 135.79 - W_EXC, 159.61 - W_EXC]
    for cx in mid_pots_res:
        res.pot_scale(cx, 75.52, r_hole=3.75, style="medium")
    res.silk.append(text(mid_pots_res[0], 86.0, "DAMPING", size=2.65, weight="700", spacing=0.25))
    res.silk.append(text(mid_pots_res[1], 86.0, "POSITION", size=2.65, weight="700", spacing=0.25))
    res.silk.append(text(mid_pots_res[2], 86.0, "SPACE", size=2.65, weight="700", spacing=0.25))

    # Attenuverter columns (5 columns on Resonator = 10 jacks)
    att_res_x = [109.79 - W_EXC, 122.81 - W_EXC, 135.79 - W_EXC, 148.81 - W_EXC, 161.79 - W_EXC]
    for ax in att_res_x:
        res.jack_graphic(ax, 95.53, r_hole=3.25, is_output=False)
        res.jack_graphic(ax, 111.08, r_hole=3.25, is_output=False)
        # Attenuverter polarity indicator − | +
        res.silk.append(line(ax - 3.9, 90.5, ax - 2.5, 90.5, w=0.18))
        res.silk.append(line(ax + 2.5, 90.5, ax + 3.9, 90.5, w=0.18))
        res.silk.append(line(ax + 3.2, 89.8, ax + 3.2, 91.2, w=0.18))
        res.silk.append(line(ax, 89.4, ax, 91.4, w=0.18))
        res.silver.append(dashed_line(ax, 95.53 + 3.25 + 1.8, ax, 111.08 - 3.25 - 1.8, w=0.28, dash="0.8,0.8"))

    # Resonator signal routing lines
    geom_x = 119.28 - W_EXC
    damp_x = 109.79 - W_EXC
    bright_x = 152.30 - W_EXC
    pts_geom = [(geom_x, 59.9), (geom_x, 70.5), (damp_x, 74.5), (damp_x, 89.0)]
    for (x1, y1), (x2, y2) in zip(pts_geom, pts_geom[1:]):
        res.silver.append(dashed_line(x1, y1, x2, y2, w=0.28, dash="0.8,0.8"))
    res.silver.append(circle(geom_x, 59.9, 0.50, fill=True))
    res.silver.append(circle(damp_x, 89.0, 0.50, fill=True))

    res.silver.append(dashed_line(bright_x, 59.9, bright_x, 89.0, w=0.28, dash="0.8,0.8"))
    res.silver.append(circle(bright_x, 59.9, 0.50, fill=True))
    res.silver.append(circle(bright_x, 89.0, 0.50, fill=True))

    # Left edge interface / bus connector (mates with Exciter)
    res.silver.append(line(2.4, 13.0, 2.4, 114.0, w=0.25))
    for py_node in (25.0, 48.0, 75.0, 95.0, 111.0):
        res.silver.append(poly([(2.4, py_node - 1.2), (0.8, py_node), (2.4, py_node + 1.2)], fill=True))
        res.silver.append(circle(4.5, py_node, 0.60, fill=True))
        res.silver.append(line(2.4, py_node, 4.5, py_node, w=0.22))

    # Resonator Footer (custom-tuned for 14HP width to avoid text overlap & avoid mount hole)
    res.hazard_stripes(W_RES - 3.0 - 18.0, 119.3, 18.0, 1.6, step=1.6, w=0.35, target=res.silk)
    res.silver.append(rect(3.0, 119.3, W_RES - 24.0, 1.6, fill=True))
    res.silk.append(line(3.0, 121.6, W_RES - 10.5, 121.6, w=0.15))
    res.silver.append(text(3.5, 121.0, "KAMMERL DSP // *CLOUDS", size=1.15, anchor="start", weight="600", spacing=0.10))
    res.silver.append(text(W_RES - 11.5, 121.0, "AUD-RES.08", size=1.15, anchor="end", weight="600", spacing=0.10))

    # Barcode & brand centered cleanly
    res.silk.append(text(32.0, 125.6, "DECØY DEVICES", size=1.95, weight="700", spacing=0.35))
    bc_x = 6.0
    for bw in [0.35, 0.2, 0.5, 0.2, 0.2, 0.4, 0.2, 0.3, 0.5, 0.2, 0.35]:
        res.silk.append(rect(bc_x, 122.5, bw, 1.5, fill=True))
        bc_x += bw + 0.30
    res.silver.append(text(6.0, 125.8, "ELM-04-H743", size=1.10, anchor="start", weight="600", spacing=0.10))

    return exc, res

def export_and_preview(exc, res):
    targets = [
        (os.path.join(OUT_DIR, "exciter"), os.path.join(OUT_DIR, "resonator"), OUT_DIR),
        (os.path.join(PCB_ART_SPLIT, "exciter"), os.path.join(PCB_ART_SPLIT, "resonator"), PCB_ART_SPLIT)
    ]

    for exc_path, res_path, root_path in targets:
        os.makedirs(exc_path, exist_ok=True)
        os.makedirs(res_path, exist_ok=True)

        exc.save_layer_svg(os.path.join(exc_path, "Exciter_F_SilkS.svg"), exc.silk, "#000000")
        exc.save_layer_svg(os.path.join(exc_path, "Exciter_F_Silver_Cu_Mask.svg"), exc.silver, "#000000")
        exc.save_edge_cuts_svg(os.path.join(exc_path, "Exciter_Edge_Cuts.svg"))
        exc.save_preview_svg(os.path.join(exc_path, "Exciter_preview.svg"))

        res.save_layer_svg(os.path.join(res_path, "Resonator_F_SilkS.svg"), res.silk, "#000000")
        res.save_layer_svg(os.path.join(res_path, "Resonator_F_Silver_Cu_Mask.svg"), res.silver, "#000000")
        res.save_edge_cuts_svg(os.path.join(res_path, "Resonator_Edge_Cuts.svg"))
        res.save_preview_svg(os.path.join(res_path, "Resonator_preview.svg"))

        # Combined Side-by-Side Rack Preview (34 HP)
        GAP = 0.3
        W_TOTAL = W_EXC + GAP + W_RES
        side_by_side = [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{W_TOTAL:.2f}mm" height="{H_PANEL}mm" viewBox="0 0 {W_TOTAL:.2f} {H_PANEL}">',
            f'  <rect width="{W_TOTAL:.2f}" height="{H_PANEL}" fill="#141416"/>',
            exc.render_preview_group(0.0, 0.0),
            res.render_preview_group(W_EXC + GAP, 0.0),
            '</svg>'
        ]
        comb_svg = os.path.join(root_path, "split_panels_preview.svg")
        with open(comb_svg, "w", encoding="utf-8") as f:
            f.write("\n".join(side_by_side))

    # Inkscape CLI conversion (export text to path & render 300 DPI PNGs)
    inkscape_bin = r"C:\Program Files\Inkscape\bin\inkscape.com"
    if os.path.exists(inkscape_bin):
        print("Running Inkscape text-to-path conversion and rendering PNG previews...")
        for _, _, root_path in targets:
            comb_svg = os.path.join(root_path, "split_panels_preview.svg")
            comb_png = os.path.join(root_path, "split_panels_preview.png")
            subprocess.run([
                inkscape_bin, comb_svg,
                "--export-text-to-path",
                "--export-plain-svg",
                f"--export-filename={comb_svg}"
            ], check=True)
            subprocess.run([
                inkscape_bin, comb_svg,
                "--export-type=png",
                "--export-dpi=300",
                f"--export-filename={comb_png}"
            ], check=True)

        for exc_path, res_path, _ in targets:
            for pfx, pdir in (("Exciter", exc_path), ("Resonator", res_path)):
                for name in ("F_SilkS", "F_Silver_Cu_Mask", "preview"):
                    svg_f = os.path.join(pdir, f"{pfx}_{name}.svg")
                    subprocess.run([
                        inkscape_bin, svg_f,
                        "--export-text-to-path",
                        "--export-plain-svg",
                        f"--export-filename={svg_f}"
                    ], check=True)
                prev_svg = os.path.join(pdir, f"{pfx}_preview.svg")
                prev_png = os.path.join(pdir, f"{pfx}_preview.png")
                subprocess.run([
                    inkscape_bin, prev_svg,
                    "--export-type=png",
                    "--export-dpi=300",
                    f"--export-filename={prev_png}"
                ], check=True)

    print(f"Exciter holes: {len(exc.holes)} (Expected: 32)")
    print(f"Resonator holes: {len(res.holes)} (Expected: 22)")
    print(f"Total holes: {len(exc.holes) + len(res.holes)} (Expected: 54)")

if __name__ == "__main__":
    exc, res = build_split_panels()
    export_and_preview(exc, res)
