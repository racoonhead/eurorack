#!/usr/bin/env python3
"""
Key_frames 20HP Panel Generator (powered by Panel_generator/panel_sdk.py)
Default Category: LIGHT -> Matte White PCB (#f2f2ee) + Black Silkscreen + Silver HASL
Usage:
  python gen_keyframes.py [--category LIGHT|AUDIO|VIDEO] [--mask white|black|purple|blue|red] [--finish silver|gold] [--out-dir PATH]
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from panel_sdk import (
    PanelCanvas, line, dashed_line, circle, arc, poly, chamfer_rect, text
)


def build_keyframes_panel(category="LIGHT", mask=None, finish=None):
    p = PanelCanvas(hp=20, category=category, mask=mask, finish=finish)
    W = p.w

    # 1. Mounting holes
    p.add_mounting_holes()

    # 2. Header (with category HUD badge & category divider line)
    p.add_header(
        title="KEY_FRAMES",
        subtitle="8CH CV SCENE CTRL // V0.1",
        sys_code="8CH.DAC",
        title_size=4.65
    )

    # 3. 8-Channel Staggered Potentiometer Matrix
    X_ROW1 = [10.70, 33.56, 56.42, 79.28]
    Y_ROW1 = 21.00
    X_ROW2 = [22.13, 44.99, 67.85, 90.71]
    Y_ROW2 = 37.50

    for i, cx in enumerate(X_ROW1):
        p.silk.append(line(cx - 2.0, 11.2, cx + 2.0, 11.2, w=0.18))
        p.silk.append(line(cx, 10.7, cx, 11.7, w=0.18))
        p.pot_scale(cx, Y_ROW1, r_hole=3.75, style="standard")
        ly = 30.65
        p.silk.append(text(cx, ly, f"CH {i + 1}", size=2.05, weight="700", spacing=0.25))
        p.silver.append(line(cx - 5.2, ly - 0.7, cx - 3.6, ly - 0.7, w=0.22))
        p.silver.append(line(cx + 3.6, ly - 0.7, cx + 5.2, ly - 0.7, w=0.22))
        p.led_indicator(cx, 35.00, r_hole=1.6)

    for i, cx in enumerate(X_ROW2):
        p.pot_scale(cx, Y_ROW2, r_hole=3.75, style="standard")
        box_y = 47.55
        p.silver.append(chamfer_rect(cx, box_y, 11.2, 3.1, c=0.75, w=0.25))
        p.silver.append(text(cx, box_y + 0.75, f"CH {i + 5}", size=2.00, weight="700", spacing=0.25))
        p.led_indicator(cx, 52.35, r_hole=1.6)

    # Staggered margin HUD callouts
    p.silver.append(poly([(4.2, 43.0), (4.2, 53.5), (8.5, 53.5)], w=0.22, close=False))
    p.silk.append(text(5.2, 47.8, "BANK // 1-4", size=1.35, anchor="start", weight="600", spacing=0.15))
    p.silk.append(text(5.2, 50.0, "BANK // 5-8", size=1.35, anchor="start", weight="600", spacing=0.15))

    p.silver.append(poly([(97.2, 13.5), (97.2, 24.5), (92.5, 24.5)], w=0.22, close=False))
    p.silk.append(text(96.0, 17.5, "QUADX2", size=1.35, anchor="end", weight="600", spacing=0.15))
    p.silk.append(text(96.0, 19.7, "12B.DAC", size=1.35, anchor="end", weight="600", spacing=0.15))

    # 4. Middle Section: Shifted Keyframe Core
    p.silver.append(poly([(3.5, 57.5), (6.0, 56.0), (36.5, 56.0)], w=0.22, close=False))
    p.silver.append(poly([(W - 3.5, 57.5), (W - 6.0, 56.0), (64.9, 56.0)], w=0.22, close=False))
    p.silk.append(circle(36.5, 56.0, 0.35, fill=True))
    p.silk.append(circle(64.9, 56.0, 0.35, fill=True))

    X_FRAME = 50.70
    Y_FRAME = 68.50
    Y_LED_FRAME = Y_FRAME - 9.525

    # Big FRAME pot (automatically includes category-specific central HUD wing brackets)
    p.pot_scale(X_FRAME, Y_FRAME, r_hole=3.75, style="big", skip_top=True)
    p.holes.append((X_FRAME, Y_LED_FRAME, 1.6, "LED_FRAME"))
    p.silver.append(circle(X_FRAME, Y_LED_FRAME, 2.15, w=0.22))
    p.silk.append(arc(X_FRAME, Y_LED_FRAME, 2.65, 195, 345, w=0.22))

    Y_FRAME_LBL = 80.20
    p.silk.append(chamfer_rect(X_FRAME, Y_FRAME_LBL, 18.0, 3.8, c=1.0, w=0.32))
    p.silk.append(text(X_FRAME, Y_FRAME_LBL + 0.85, "FRAME", size=2.35, weight="700", spacing=0.40))
    p.silver.append(line(X_FRAME - 12.5, Y_FRAME_LBL, X_FRAME - 9.6, Y_FRAME_LBL, w=0.30))
    p.silver.append(line(X_FRAME + 9.6, Y_FRAME_LBL, X_FRAME + 12.5, Y_FRAME_LBL, w=0.30))

    # Left: ADD & DEL Buttons + KEY LED
    X_BTN = 16.50
    Y_ADD = 61.00
    Y_DEL = 74.20
    X_LED_KEY = 31.00
    Y_LED_KEY = Y_FRAME

    p.holes.append((X_BTN, Y_ADD, 2.65, "BTN_ADD"))
    p.silver.append(circle(X_BTN, Y_ADD, 3.55, w=0.25))
    p.silk.append(circle(X_BTN, Y_ADD, 4.15, w=0.32))
    p.silver.append(line(X_BTN - 6.4, Y_ADD, X_BTN - 5.0, Y_ADD, w=0.28))
    p.silver.append(line(X_BTN - 5.7, Y_ADD - 0.7, X_BTN - 5.7, Y_ADD + 0.7, w=0.28))
    p.silk.append(text(X_BTN, Y_ADD + 6.3, "ADD", size=1.95, weight="700", spacing=0.30))

    p.holes.append((X_BTN, Y_DEL, 2.65, "BTN_DEL"))
    p.silver.append(circle(X_BTN, Y_DEL, 3.55, w=0.25))
    p.silk.append(circle(X_BTN, Y_DEL, 4.15, w=0.32))
    p.silver.append(line(X_BTN - 6.4, Y_DEL, X_BTN - 5.0, Y_DEL, w=0.28))
    p.silk.append(text(X_BTN, Y_DEL + 6.3, "DEL", size=1.95, weight="700", spacing=0.30))

    p.led_indicator(X_LED_KEY, Y_LED_KEY, r_hole=1.6)
    p.silver.append(text(X_LED_KEY, Y_LED_KEY + 4.8, "KEY", size=1.55, weight="600", spacing=0.20))

    p.silver.append(poly([
        (X_BTN + 4.5, Y_ADD),
        (X_LED_KEY - 3.5, Y_ADD),
        (X_LED_KEY - 1.5, Y_LED_KEY - 3.0)
    ], w=0.22, close=False))
    p.silver.append(poly([
        (X_BTN + 4.5, Y_DEL),
        (X_LED_KEY - 3.5, Y_DEL),
        (X_LED_KEY - 1.5, Y_LED_KEY + 3.0)
    ], w=0.22, close=False))
    p.silver.append(line(X_LED_KEY + 3.0, Y_LED_KEY, X_FRAME - 14.8, Y_LED_KEY, w=0.25))

    # Right: MODULATION Attenuverter Pot
    X_MOD = 84.50
    Y_MOD = Y_FRAME

    p.pot_scale(X_MOD, Y_MOD, r_hole=3.75, style="medium")
    p.silver.append(line(X_MOD - 4.8, Y_MOD + 6.8, X_MOD - 3.4, Y_MOD + 6.8, w=0.28))
    p.silver.append(line(X_MOD + 3.4, Y_MOD + 6.8, X_MOD + 4.8, Y_MOD + 6.8, w=0.28))
    p.silver.append(line(X_MOD + 4.1, Y_MOD + 6.1, X_MOD + 4.1, Y_MOD + 7.5, w=0.28))
    p.silk.append(text(X_MOD, 79.2, "MODULATION", size=1.95, weight="700", spacing=0.22))
    p.silver.append(line(X_MOD - 7.5, 80.2, X_MOD + 7.5, 80.2, w=0.20))
    p.silver.append(line(X_FRAME + 14.8, Y_FRAME, X_MOD - 8.2, Y_FRAME, w=0.25))

    # 5. Jack Patchbay Section
    p.silver.append(line(3.5, 84.8, 33.5, 84.8, w=0.30))
    p.silver.append(line(67.9, 84.8, W - 3.5, 84.8, w=0.30))
    p.silk.append(line(3.5, 84.8, 3.5, 86.6, w=0.30))
    p.silk.append(line(W - 3.5, 84.8, W - 3.5, 86.6, w=0.30))
    p.silk.append(text(50.70, 85.4, "CV IN // 8CH SCENE OUTPUTS", size=1.65, weight="600", spacing=0.25))

    p.silver.append(dashed_line(24.8, 86.8, 24.8, 117.2, w=0.22, dash="1.0,0.9"))

    Y_JACK_TOP = 93.00
    Y_JACK_BOT = 108.20
    X_COL0 = 14.20

    p.jack_graphic(X_COL0, Y_JACK_TOP, r_hole=3.2, is_output=False)
    p.silk.append(text(X_COL0, 100.8, "FRAME", size=1.95, weight="700", spacing=0.25))
    p.silver.append(line(X_COL0 - 4.5, 101.6, X_COL0 + 4.5, 101.6, w=0.20))

    p.jack_graphic(X_COL0, Y_JACK_BOT, r_hole=3.2, is_output=True)
    p.silk.append(chamfer_rect(X_COL0, 115.6, 13.0, 3.2, c=0.8, w=0.28))
    p.silk.append(text(X_COL0, 116.35, "STEP", size=1.95, weight="700", spacing=0.28))

    X_OUTS = [34.80, 52.80, 70.80, 88.80]
    for i, jx in enumerate(X_OUTS):
        p.silver.append(dashed_line(jx, 102.4, jx, 102.9, w=0.20, dash="0.4,0.4"))
        p.jack_graphic(jx, Y_JACK_TOP, r_hole=3.2, is_output=True)
        p.silver.append(chamfer_rect(jx, 100.4, 13.6, 3.2, c=0.8, w=0.28))
        p.silver.append(text(jx, 101.15, f"OUT {i + 1}", size=1.95, weight="700", spacing=0.25))

        p.jack_graphic(jx, Y_JACK_BOT, r_hole=3.2, is_output=True)
        p.silk.append(chamfer_rect(jx, 115.6, 13.6, 3.2, c=0.8, w=0.28))
        p.silk.append(text(jx, 116.35, f"OUT {i + 5}", size=1.95, weight="700", spacing=0.25))

    # 6. Footer (with category-specific pattern & center emblem)
    p.add_footer(serial_left="DD-KF01 // REV 0.1", serial_right="KFR-01-STM32")
    return p


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate Key_frames 20HP PCB Front Panel")
    parser.add_argument("--category", default="LIGHT", choices=["LIGHT", "AUDIO", "VIDEO"],
                        help="Module category (LIGHT=white, AUDIO=black, VIDEO=purple)")
    parser.add_argument("--mask", default=None, choices=["white", "black", "purple", "blue", "red"],
                        help="Override PCB solder mask color (defaults to category standard)")
    parser.add_argument("--finish", default="silver", choices=["silver", "gold"],
                        help="Exposed copper surface finish (silver HASL or gold ENIG)")
    parser.add_argument("--out-dir", default=os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "Key_frames", "hardware_design", "panel", "pcb_art")
    ), help="Output directory for SVG and PNG files")
    args = parser.parse_args()

    panel = build_keyframes_panel(category=args.category, mask=args.mask, finish=args.finish)
    panel.export_all(args.out_dir)
