#!/usr/bin/env python3
"""
DECØY DEVICES — Universal Eurorack PCB Panel Generator SDK
Unified HUD design system with deep multi-element visual differentiation across 3 categories:
  1. AUDIO (Synth / DSP)      -> Default: Matte BLACK PCB (#0c0c0e) + White Silk + Silver Copper
  2. LIGHT (DMX / Stage CV)   -> Default: Matte WHITE PCB (#f2f2ee) + Black Silk + Silver Copper
  3. VIDEO (RGB / Sync / LZX) -> Default: Deep PURPLE PCB (#190d2e) + White Silk + Silver/Gold Copper

Differentiated across 6 coordinated elements within the same unified layout grid:
  - PCB Solder Mask & Silkscreen polarity (Black / White / Purple)
  - Header HUD Category Badge & Divider Line motif
  - Potentiometer Scale & Big Knob Central HUD Emblem
  - LED Indicator Window Collar (Concentric / 4-Ray Sunburst / Pixel Diamond)
  - 3.5mm Jack Surrounds (Circular / Octagonal Aperture / Viewfinder Brackets)
  - Footer Technical Bar Pattern & Center Cutout Emblem
"""
import math
import os
import subprocess

FONT = "Bahnschrift"

# ======================== COLOR & CATEGORY THEMES ========================

MASK_THEMES = {
    "black": {
        "bg": "#0c0c0e",
        "silk": "#f4f4f0",
        "silver_override": None,
        "hole": "#050507",
        "hole_rim": "#25262b",
        "border": "#2a2b30",
        "name": "Matte Black (AUDIO Standard)"
    },
    "white": {
        "bg": "#f2f2ee",
        "silk": "#111215",
        "silver_override": "#7a828e",  # Metallic silver/tin contrast on white solder mask
        "hole": "#0a0b0d",
        "hole_rim": "#c2c4be",
        "border": "#c8c8c2",
        "name": "Matte White (LIGHT Standard)"
    },
    "purple": {
        "bg": "#190d2e",
        "silk": "#f4f4f0",
        "silver_override": None,
        "hole": "#080410",
        "hole_rim": "#392263",
        "border": "#392263",
        "name": "Cyber Violet / Purple (VIDEO Standard)"
    },
    "blue": {
        "bg": "#0a1526",
        "silk": "#f4f4f0",
        "silver_override": None,
        "hole": "#040810",
        "hole_rim": "#1e3252",
        "border": "#1e3252",
        "name": "Deep Navy Blue"
    },
    "red": {
        "bg": "#1e090d",
        "silk": "#f4f4f0",
        "silver_override": None,
        "hole": "#0c0305",
        "hole_rim": "#421720",
        "border": "#421720",
        "name": "Deep Crimson"
    },
}

FINISH_THEMES = {
    "silver": {"fg": "#b9bec7", "name": "HASL / Immersion Tin (Silver)"},
    "gold":   {"fg": "#d6b24c", "name": "ENIG (Immersion Gold)"},
}

CATEGORIES = {
    "AUDIO": {
        "code": "AUD",
        "tag": "AUDIO // DSP.SYNTH",
        "default_mask": "black",
        "default_finish": "silver",
        "description": "Audio Oscillators, Filters, VCAs & DSP Processors (Matte Black PCB)",
    },
    "LIGHT": {
        "code": "LUX",
        "tag": "LIGHT // DMX.CV",
        "default_mask": "white",
        "default_finish": "silver",
        "description": "Stage Lighting, DMX512 & Fixture CV Controllers (Matte White PCB)",
    },
    "VIDEO": {
        "code": "VID",
        "tag": "VIDEO // RGB.SYNC",
        "default_mask": "purple",
        "default_finish": "silver",
        "description": "Video Synthesizers, Sync Generators & RGB Scan Processors (Purple PCB)",
    },
}


# ======================== LOW-LEVEL SVG PRIMITIVES ========================

def line(x1, y1, x2, y2, w=0.25, cap="round"):
    return (f'<line x1="{x1:.3f}" y1="{y1:.3f}" x2="{x2:.3f}" y2="{y2:.3f}" '
            f'stroke="CURR" stroke-width="{w:.3f}" stroke-linecap="{cap}"/>')


def dashed_line(x1, y1, x2, y2, w=0.22, dash="0.8,0.8"):
    return (f'<line x1="{x1:.3f}" y1="{y1:.3f}" x2="{x2:.3f}" y2="{y2:.3f}" '
            f'stroke="CURR" stroke-width="{w:.3f}" stroke-dasharray="{dash}" stroke-linecap="butt"/>')


def circle(cx, cy, r, w=0.25, fill=False):
    if fill:
        return f'<circle cx="{cx:.3f}" cy="{cy:.3f}" r="{r:.3f}" fill="CURR"/>'
    return f'<circle cx="{cx:.3f}" cy="{cy:.3f}" r="{r:.3f}" fill="none" stroke="CURR" stroke-width="{w:.3f}"/>'


def arc(cx, cy, r, a1_deg, a2_deg, w=0.25, cap="round"):
    a1 = math.radians(a1_deg)
    a2 = math.radians(a2_deg)
    x1, y1 = cx + r * math.cos(a1), cy + r * math.sin(a1)
    x2, y2 = cx + r * math.cos(a2), cy + r * math.sin(a2)
    large = 1 if (a2_deg - a1_deg) % 360 > 180 else 0
    return (f'<path d="M {x1:.3f} {y1:.3f} A {r:.3f} {r:.3f} 0 {large} 1 {x2:.3f} {y2:.3f}" '
            f'fill="none" stroke="CURR" stroke-width="{w:.3f}" stroke-linecap="{cap}"/>')


def rect(x, y, rw, rh, w=0.25, fill=False, rx=0):
    rx_s = f' rx="{rx:.3f}"' if rx > 0 else ''
    if fill:
        return f'<rect x="{x:.3f}" y="{y:.3f}" width="{rw:.3f}" height="{rh:.3f}"{rx_s} fill="CURR"/>'
    return (f'<rect x="{x:.3f}" y="{y:.3f}" width="{rw:.3f}" height="{rh:.3f}"{rx_s} '
            f'fill="none" stroke="CURR" stroke-width="{w:.3f}"/>')


def poly(pts, w=0.25, fill=False, close=True):
    pts_s = " ".join(f"{p[0]:.3f},{p[1]:.3f}" for p in pts)
    if fill:
        return f'<polygon points="{pts_s}" fill="CURR"/>'
    tag = "polygon" if close else "polyline"
    return (f'<{tag} points="{pts_s}" fill="none" stroke="CURR" stroke-width="{w:.3f}" '
            f'stroke-linejoin="round" stroke-linecap="round"/>')


def chamfer_rect(cx, cy, rw, rh, c=0.9, w=0.25, fill=False):
    x0, y0 = cx - rw / 2, cy - rh / 2
    x1, y1 = cx + rw / 2, cy + rh / 2
    pts = [
        (x0 + c, y0), (x1 - c, y0),
        (x1, y0 + c), (x1, y1 - c),
        (x1 - c, y1), (x0 + c, y1),
        (x0, y1 - c), (x0, y0 + c)
    ]
    return poly(pts, w=w, fill=fill, close=True)


def octagon(cx, cy, r, w=0.25, fill=False, rot_deg=22.5):
    pts = []
    for i in range(8):
        a = math.radians(rot_deg + i * 45.0)
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return poly(pts, w=w, fill=fill, close=True)


def diamond(cx, cy, rx, ry, w=0.25, fill=False):
    pts = [(cx, cy - ry), (cx + rx, cy), (cx, cy + ry), (cx - rx, cy)]
    return poly(pts, w=w, fill=fill, close=True)


def text(x, y, s, size=2.3, anchor="middle", weight="600", spacing=0.25):
    s_esc = s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return (f'<text x="{x:.3f}" y="{y:.3f}" font-family="{FONT}" font-weight="{weight}" '
            f'font-stretch="semi-condensed" font-size="{size:.3f}" fill="CURR" '
            f'text-anchor="{anchor}" letter-spacing="{spacing:.3f}">{s_esc}</text>')


# ======================== PANEL CANVAS CLASS ========================

class PanelCanvas:
    def __init__(self, hp=20, category="LIGHT", mask=None, finish=None):
        self.hp = hp
        self.w = round(hp * 5.08 - 0.2, 2) if hp != 20 else 101.4
        self.h = 128.5
        self.category = category.upper()
        if self.category not in CATEGORIES:
            raise ValueError(f"Unknown category '{category}'. Choose from: {list(CATEGORIES.keys())}")

        cat_info = CATEGORIES[self.category]
        self.mask_name = (mask or cat_info["default_mask"]).lower()
        self.finish_name = (finish or cat_info["default_finish"]).lower()

        self.mask_theme = MASK_THEMES.get(self.mask_name, MASK_THEMES["black"])
        self.finish_theme = FINISH_THEMES.get(self.finish_name, FINISH_THEMES["silver"])

        self.silk_color = self.mask_theme["silk"]
        if self.finish_name == "silver" and self.mask_theme.get("silver_override"):
            self.silver_color = self.mask_theme["silver_override"]
        else:
            self.silver_color = self.finish_theme["fg"]

        self.silk = []
        self.silver = []
        self.holes = []

    def add_mounting_holes(self):
        positions = [(7.5, 3.0), (self.w - 7.5, 3.0), (7.5, self.h - 3.0), (self.w - 7.5, self.h - 3.0)]
        for mx, my in positions:
            self.holes.append((mx, my, 1.6, "MOUNT"))
            self.silver.append(circle(mx, my, 2.55, w=0.20))

    # ======================== 1. CATEGORY HEADER & BADGE ========================

    def draw_category_badge(self, cx, cy):
        """Draws a distinct 5.2x5.2mm HUD icon in the same unified octagonal/reticle frame."""
        if self.category == "AUDIO":
            # AUDIO: Chamfered frame + Oscilloscope Sine Wave
            self.silver.append(chamfer_rect(cx, cy, 5.2, 5.2, c=1.1, w=0.25))
            self.silver.append(dashed_line(cx - 2.0, cy, cx + 2.0, cy, w=0.15, dash="0.4,0.4"))
            pts = []
            for i in range(25):
                t = i / 24.0
                px = (cx - 1.95) + t * 3.90
                py = cy - math.sin(t * 2.0 * math.pi) * 1.50
                pts.append((px, py))
            self.silk.append(poly(pts, w=0.30, close=False))

        elif self.category == "LIGHT":
            # LIGHT: Chamfered frame + Stage Lens Aperture + 5 Photometric Beam Rays
            self.silver.append(chamfer_rect(cx, cy, 5.2, 5.2, c=1.1, w=0.25))
            self.silk.append(circle(cx - 1.0, cy, 1.10, w=0.28))
            self.silver.append(circle(cx - 1.0, cy, 0.38, fill=True))
            for deg in (-36, -18, 0, 18, 36):
                a = math.radians(deg)
                x1 = (cx - 1.0) + 1.40 * math.cos(a)
                y1 = cy + 1.40 * math.sin(a)
                x2 = (cx - 1.0) + 2.55 * math.cos(a)
                y2 = cy + 2.55 * math.sin(a)
                self.silk.append(line(x1, y1, x2, y2, w=0.22))

        elif self.category == "VIDEO":
            # VIDEO: Chamfered frame + Viewfinder Corner Brackets + RGB Sync Pulse
            self.silver.append(chamfer_rect(cx, cy, 5.2, 5.2, c=1.1, w=0.25))
            b, s = 1.95, 0.85
            for sx in (-1, 1):
                for sy in (-1, 1):
                    self.silk.append(poly([
                        (cx + sx * b, cy + sy * (b - s)),
                        (cx + sx * b, cy + sy * b),
                        (cx + sx * (b - s), cy + sy * b)
                    ], w=0.25, close=False))
            self.silver.append(line(cx - 1.3, cy - 0.85, cx + 1.3, cy - 0.85, w=0.16))
            self.silk.append(poly([
                (cx - 1.4, cy + 0.15), (cx - 0.55, cy + 0.15),
                (cx - 0.25, cy - 0.65), (cx + 0.25, cy + 0.65),
                (cx + 0.55, cy + 0.15), (cx + 1.4, cy + 0.15)
            ], w=0.24, close=False))
            self.silver.append(line(cx - 1.3, cy + 0.95, cx + 1.3, cy + 0.95, w=0.16))

    def add_header(self, title, subtitle, sys_code="SYS.01", title_size=4.65):
        """Unified top header (Y = 0..10.8 mm) with category-specific divider & right marker."""
        self.draw_category_badge(14.8, 4.0)

        self.silk.append(text(18.8, 5.8, title, size=title_size, anchor="start", weight="700", spacing=0.55))
        self.silver.append(line(18.8, 1.3, 56.5, 1.3, w=0.22))
        self.silver.append(line(32.0, 6.85, 57.5, 6.85, w=0.18))

        self.silver.append(text(59.5, 3.45, subtitle, size=1.80, anchor="start", weight="600", spacing=0.15))
        bx = 59.5
        for bw in [1.4, 0.5, 0.9, 2.0, 0.5, 0.5, 1.3, 0.6, 1.6]:
            self.silk.append(rect(bx, 4.45, bw, 1.35, fill=True))
            bx += bw + 0.50
        cat_code = CATEGORIES[self.category]["code"]
        self.silver.append(text(74.2, 5.65, f"{cat_code}.{sys_code}", size=1.35, anchor="start", weight="600", spacing=0.14))

        # Primary silver header line + corner brackets (shared across all modules)
        self.silver.append(line(3.0, 8.2, self.w - 3.0, 8.2, w=0.40))
        self.silk.append(line(3.0, 8.2, 3.0, 10.6, w=0.30))
        self.silk.append(line(3.0, 9.8, 5.2, 9.8, w=0.25))
        self.silk.append(line(self.w - 3.0, 8.2, self.w - 3.0, 10.6, w=0.30))
        self.silk.append(line(self.w - 3.0, 9.8, self.w - 5.2, 9.8, w=0.25))

        if self.category == "AUDIO":
            # AUDIO: Continuous double line + '>>>' chevrons
            self.silver.append(line(3.0, 9.0, self.w - 3.0, 9.0, w=0.15))
            for i in range(3):
                ax = self.w - 10.0 + i * 1.4
                self.silk.append(poly([(ax, 9.5), (ax + 0.8, 10.1), (ax, 10.7)], w=0.25, close=False))

        elif self.category == "LIGHT":
            # LIGHT: Segmented optical beam line with diamond nodes + 3 diamond markers on right
            self.silver.append(dashed_line(3.0, 9.0, self.w - 3.0, 9.0, w=0.20, dash="3.2,1.2"))
            for i in range(3):
                dx = self.w - 9.8 + i * 1.6
                self.silk.append(diamond(dx, 10.1, 0.55, 0.55, w=0.22, fill=True))

        elif self.category == "VIDEO":
            # VIDEO: H-Sync digital pulse train + registration crosshairs '+ + +' on right
            pts = [(3.0, 9.0), (12.0, 9.0)]
            x_cur = 12.0
            while x_cur < self.w - 15.0:
                pts.extend([
                    (x_cur, 9.0), (x_cur, 9.65),
                    (x_cur + 2.2, 9.65), (x_cur + 2.2, 9.0),
                    (x_cur + 5.5, 9.0)
                ])
                x_cur += 5.5
            pts.append((self.w - 3.0, 9.0))
            self.silver.append(poly(pts, w=0.16, close=False))
            for i in range(3):
                cx_m = self.w - 10.0 + i * 1.7
                cy_m = 10.1
                self.silk.append(line(cx_m - 0.5, cy_m, cx_m + 0.5, cy_m, w=0.22))
                self.silk.append(line(cx_m, cy_m - 0.5, cx_m, cy_m + 0.5, w=0.22))

    # ======================== 2. POTENTIOMETERS & CENTRAL EMBLEM ========================

    def pot_scale(self, cx, cy, r_hole=3.75, style="standard", skip_top=False):
        """Unified 270° pot scale with category-distinct tick & ring geometry."""
        self.holes.append((cx, cy, r_hole, "POT"))

        if style == "big":
            # Inner ring (shared radius 6.8mm, gap at top if skip_top)
            if skip_top:
                self.silver.append(arc(cx, cy, 6.8, 294, 606, w=0.35))
            else:
                self.silver.append(arc(cx, cy, 6.8, 135, 405, w=0.35))

            n_ticks = 23
            for i in range(n_ticks):
                if skip_top and i in (10, 11, 12):
                    continue
                deg = 135 + i * (270.0 / (n_ticks - 1))
                a = math.radians(deg)
                is_major = (i % 2 == 0)
                r1 = 8.4 if is_major else 8.8
                r2 = 10.3 if is_major else 9.7
                w = 0.35 if is_major else 0.20
                x1, y1 = cx + r1 * math.cos(a), cy + r1 * math.sin(a)
                x2, y2 = cx + r2 * math.cos(a), cy + r2 * math.sin(a)

                if self.category == "LIGHT" and is_major and i not in (0, n_ticks - 1):
                    # LIGHT: Photometric ray + outer diamond node on cardinal/even ticks
                    self.silver.append(line(x1, y1, x2, y2, w=w))
                    if i % 4 == 0:
                        dx, dy = cx + 10.8 * math.cos(a), cy + 10.8 * math.sin(a)
                        self.silk.append(circle(dx, dy, 0.32, fill=True))
                elif self.category == "VIDEO" and is_major and i % 4 == 0:
                    # VIDEO: Reticle T-bar ticks on major video graticule positions
                    self.silk.append(line(x1, y1, x2, y2, w=0.38))
                    tx = -math.sin(a) * 0.55
                    ty = math.cos(a) * 0.55
                    self.silver.append(line(x2 - tx, y2 - ty, x2 + tx, y2 + ty, w=0.22))
                else:
                    if i in (0, n_ticks - 1):
                        self.silk.append(line(x1, y1, x2, y2, w=0.45))
                    elif is_major:
                        self.silver.append(line(x1, y1, x2, y2, w=w))
                    else:
                        self.silk.append(line(x1, y1, x2, y2, w=w))

            # Outer flank arcs & Central HUD Wing Brackets (Category-Specific!)
            self.silk.append(arc(cx, cy, 11.2, 145, 232, w=0.22))
            self.silk.append(arc(cx, cy, 11.2, 308, 395, w=0.22))

            for dx in (-1, 1):
                bx1 = cx + dx * 12.2
                bx2 = cx + dx * 14.2
                if self.category == "AUDIO":
                    # AUDIO: Chamfered wing brackets + vertical bar
                    self.silver.append(poly([
                        (bx1, cy - 6.0), (bx2, cy - 4.0),
                        (bx2, cy + 4.0), (bx1, cy + 6.0)
                    ], w=0.28, close=False))
                    self.silk.append(line(cx + dx * 13.0, cy - 2.2, cx + dx * 13.0, cy + 2.2, w=0.22))
                elif self.category == "LIGHT":
                    # LIGHT: Faceted Prism / Fresnel wing + 3 radiating light rays (zero silk/silver overlap)
                    self.silver.append(poly([
                        (bx1, cy - 6.2), (bx2, cy - 3.2), (bx1 + dx * 0.8, cy),
                        (bx2, cy + 3.2), (bx1, cy + 6.2)
                    ], w=0.28, close=False))
                    for ry in (-2.2, 0.0, 2.2):
                        self.silk.append(line(cx + dx * 11.55, cy + ry * 0.85, cx + dx * 12.35, cy + ry, w=0.22))
                elif self.category == "VIDEO":
                    # VIDEO: Square CRT Aspect Corner Brackets + Center Sync Crosshair
                    self.silver.append(poly([
                        (bx1, cy - 6.0), (bx2, cy - 6.0), (bx2, cy - 2.2)
                    ], w=0.28, close=False))
                    self.silver.append(poly([
                        (bx2, cy + 2.2), (bx2, cy + 6.0), (bx1, cy + 6.0)
                    ], w=0.28, close=False))
                    ch_x = cx + dx * 13.2
                    self.silk.append(line(ch_x - 0.7, cy, ch_x + 0.7, cy, w=0.22))
                    self.silk.append(line(ch_x, cy - 0.7, ch_x, cy + 0.7, w=0.22))

        elif style == "standard":
            if self.category == "AUDIO":
                # AUDIO: Continuous silver inner arc + classic radial ticks
                self.silver.append(arc(cx, cy, 5.6, 135, 405, w=0.28))
                n_ticks = 15
                for i in range(n_ticks):
                    a = math.radians(135 + i * (270.0 / (n_ticks - 1)))
                    is_major = (i in (0, 7, 14))
                    is_mid = (i % 2 == 1)
                    r1 = 6.3
                    r2 = 8.1 if is_major else (7.5 if is_mid else 7.1)
                    w = 0.35 if is_major else 0.18
                    x1, y1 = cx + r1 * math.cos(a), cy + r1 * math.sin(a)
                    x2, y2 = cx + r2 * math.cos(a), cy + r2 * math.sin(a)
                    if is_major:
                        self.silk.append(line(x1, y1, x2, y2, w=w))
                    else:
                        self.silver.append(line(x1, y1, x2, y2, w=w))

            elif self.category == "LIGHT":
                # LIGHT: Segmented photometric halo arc + radial beam ticks + cardinal beam dots
                for seg_a1, seg_a2 in [(138, 198), (206, 266), (274, 334), (342, 402)]:
                    self.silver.append(arc(cx, cy, 5.6, seg_a1, seg_a2, w=0.28))
                n_ticks = 15
                for i in range(n_ticks):
                    a = math.radians(135 + i * (270.0 / (n_ticks - 1)))
                    is_major = (i in (0, 7, 14))
                    is_mid = (i % 2 == 1)
                    r1 = 6.3
                    r2 = 8.1 if is_major else (7.4 if is_mid else 7.0)
                    x1, y1 = cx + r1 * math.cos(a), cy + r1 * math.sin(a)
                    x2, y2 = cx + r2 * math.cos(a), cy + r2 * math.sin(a)
                    if is_major:
                        self.silk.append(line(x1, y1, x2, y2, w=0.36))
                    elif is_mid:
                        self.silk.append(circle(cx + 7.35 * math.cos(a), cy + 7.35 * math.sin(a), 0.24, fill=True))
                    else:
                        self.silver.append(line(x1, y1, x2, y2, w=0.18))

            elif self.category == "VIDEO":
                # VIDEO: Inner & outer graticule arcs + orthogonal T-ticks at major positions
                self.silver.append(arc(cx, cy, 5.6, 135, 405, w=0.26))
                self.silver.append(arc(cx, cy, 7.6, 150, 250, w=0.16))
                self.silver.append(arc(cx, cy, 7.6, 290, 390, w=0.16))
                n_ticks = 15
                for i in range(n_ticks):
                    a = math.radians(135 + i * (270.0 / (n_ticks - 1)))
                    is_major = (i in (0, 7, 14))
                    r1 = 6.2
                    r2 = 8.1 if is_major else 7.2
                    x1, y1 = cx + r1 * math.cos(a), cy + r1 * math.sin(a)
                    x2, y2 = cx + r2 * math.cos(a), cy + r2 * math.sin(a)
                    if is_major:
                        self.silk.append(line(x1, y1, x2, y2, w=0.35))
                        tx, ty = -math.sin(a) * 0.45, math.cos(a) * 0.45
                        self.silk.append(line(x2 - tx, y2 - ty, x2 + tx, y2 + ty, w=0.22))
                    else:
                        self.silver.append(line(x1, y1, x2, y2, w=0.18))

        elif style == "medium":
            self.silver.append(arc(cx, cy, 5.2, 135, 405, w=0.25))
            n_ticks = 11
            for i in range(n_ticks):
                a = math.radians(135 + i * (270.0 / (n_ticks - 1)))
                is_major = (i in (0, 5, 10))
                r1 = 5.9
                r2 = 7.4 if is_major else 6.8
                w = 0.32 if is_major else 0.18
                x1, y1 = cx + r1 * math.cos(a), cy + r1 * math.sin(a)
                x2, y2 = cx + r2 * math.cos(a), cy + r2 * math.sin(a)
                if is_major:
                    self.silk.append(line(x1, y1, x2, y2, w=w))
                else:
                    self.silver.append(line(x1, y1, x2, y2, w=w))

    # ======================== 3. LED INDICATORS ========================

    def led_indicator(self, cx, cy, r_hole=1.6):
        """Unified 3mm LED window with category-specific outer collar."""
        self.holes.append((cx, cy, r_hole, "LED"))
        self.silver.append(circle(cx, cy, r_hole + 0.55, w=0.22))

        if self.category == "AUDIO":
            # Concentric outer silk ring
            self.silk.append(circle(cx, cy, r_hole + 1.00, w=0.18))
        elif self.category == "LIGHT":
            # Outer silk ring + 4 cardinal photometric ray ticks
            r_out = r_hole + 0.95
            self.silk.append(circle(cx, cy, r_out, w=0.18))
            for deg in (0, 90, 180, 270):
                a = math.radians(deg)
                self.silk.append(line(
                    cx + (r_out + 0.15) * math.cos(a), cy + (r_out + 0.15) * math.sin(a),
                    cx + (r_out + 0.55) * math.cos(a), cy + (r_out + 0.55) * math.sin(a),
                    w=0.20
                ))
        elif self.category == "VIDEO":
            # Chamfered square / pixel bracket around the LED ring
            self.silk.append(chamfer_rect(cx, cy, (r_hole + 0.95) * 2, (r_hole + 0.95) * 2, c=0.8, w=0.18))

    # ======================== 4. JACK SURROUNDS ========================

    def jack_graphic(self, cx, cy, r_hole=3.2, is_output=False):
        """Unified 3.5mm jack socket graphic with category-specific outer bezel."""
        self.holes.append((cx, cy, r_hole, "JACK"))

        if self.category == "AUDIO":
            # AUDIO: Pure concentric circular rings
            if is_output:
                self.silver.append(circle(cx, cy, 4.55, w=0.38))
                self.silk.append(circle(cx, cy, 5.15, w=0.20))
            else:
                self.silk.append(circle(cx, cy, 4.55, w=0.28))
                self.silver.append(arc(cx, cy, 5.15, -45, 225, w=0.22))

        elif self.category == "LIGHT":
            # LIGHT: Circular inner ring + Octagonal faceted aperture outer bezel
            if is_output:
                self.silver.append(circle(cx, cy, 4.50, w=0.38))
                self.silk.append(octagon(cx, cy, 5.25, w=0.22))
            else:
                self.silk.append(circle(cx, cy, 4.50, w=0.28))
                self.silver.append(arc(cx, cy, 5.10, -45, 225, w=0.20))
                # 4 diagonal prism ticks
                for deg in (45, 135, 225, 315):
                    a = math.radians(deg)
                    self.silk.append(line(
                        cx + 4.8 * math.cos(a), cy + 4.8 * math.sin(a),
                        cx + 5.4 * math.cos(a), cy + 5.4 * math.sin(a),
                        w=0.22
                    ))

        elif self.category == "VIDEO":
            # VIDEO: Circular inner ring + CRT Viewfinder Corner Brackets [ ]
            if is_output:
                self.silver.append(circle(cx, cy, 4.50, w=0.38))
                b, s = 5.05, 1.55
                for sx in (-1, 1):
                    for sy in (-1, 1):
                        self.silk.append(poly([
                            (cx + sx * b, cy + sy * (b - s)),
                            (cx + sx * b, cy + sy * b),
                            (cx + sx * (b - s), cy + sy * b)
                        ], w=0.24, close=False))
            else:
                self.silk.append(circle(cx, cy, 4.50, w=0.28))
                self.silver.append(arc(cx, cy, 5.10, -45, 225, w=0.20))
                # 4 cardinal sync reticle ticks (0, 90, 180, 270 deg)
                for deg in (0, 90, 180, 270):
                    a = math.radians(deg)
                    self.silk.append(line(
                        cx + 4.75 * math.cos(a), cy + 4.75 * math.sin(a),
                        cx + 5.45 * math.cos(a), cy + 5.45 * math.sin(a),
                        w=0.24
                    ))

    # ======================== 5. FOOTER SECTION ========================

    def add_footer(self, serial_left="DD-MOD01 // REV 0.1", serial_right="STM32", brand="DECØY DEVICES"):
        """Unified bottom footer (Y = 119.3..128.5 mm) with category-distinct bar & center emblem."""
        cat_code = CATEGORIES[self.category]["code"]
        W = self.w
        side_w = 23.0 if W >= 95.0 else 16.0
        bar_x0 = 3.0 + side_w + 2.0
        bar_seg_w = (W / 2 - 3.2) - bar_x0

        if self.category == "AUDIO":
            # AUDIO: 45° diagonal hazard stripes + solid silver bar + central diamond
            self.hazard_stripes(3.0, 119.3, side_w, 1.6, step=1.6, w=0.35, target=self.silk)
            self.hazard_stripes(W - 3.0 - side_w, 119.3, side_w, 1.6, step=1.6, w=0.35, target=self.silk)
            self.silver.append(rect(bar_x0, 119.3, bar_seg_w, 1.6, fill=True))
            self.silver.append(rect(W / 2 + 3.2, 119.3, bar_seg_w, 1.6, fill=True))
            self.silk.append(diamond(W / 2, 120.1, 1.8, 1.0, w=0.25, fill=True))

        elif self.category == "LIGHT":
            # LIGHT: Opposing optical beam chevrons (>>>> | <<<<) + solid silver bar + sunburst prism
            n_chev = int(side_w / 1.8)
            for i in range(n_chev):
                lx = 3.4 + i * 1.75
                rx = (W - 3.4) - i * 1.75
                self.silk.append(poly([(lx, 119.35), (lx + 0.9, 120.1), (lx, 120.85)], w=0.30, close=False))
                self.silk.append(poly([(rx, 119.35), (rx - 0.9, 120.1), (rx, 120.85)], w=0.30, close=False))
            self.silver.append(rect(bar_x0, 119.3, bar_seg_w, 1.6, fill=True))
            self.silver.append(rect(W / 2 + 3.2, 119.3, bar_seg_w, 1.6, fill=True))
            # Sunburst double-diamond + center dot
            self.silk.append(diamond(W / 2, 120.1, 2.0, 1.05, w=0.24, fill=False))
            self.silk.append(circle(W / 2, 120.1, 0.45, fill=True))

        elif self.category == "VIDEO":
            # VIDEO: Dual-row SMPTE checkerboard sync blocks + solid silver bar + CRT aspect reticle [•]
            n_cols = int(side_w / 1.6)
            for col in range(n_cols):
                lx = 3.0 + col * 1.6
                rx = (W - 3.0 - n_cols * 1.6) + col * 1.6
                y_off = 119.3 if (col % 2 == 0) else 120.1
                self.silk.append(rect(lx, y_off, 1.35, 0.8, fill=True))
                self.silk.append(rect(rx, y_off, 1.35, 0.8, fill=True))
            self.silver.append(rect(bar_x0, 119.3, bar_seg_w, 1.6, fill=True))
            self.silver.append(rect(W / 2 + 3.2, 119.3, bar_seg_w, 1.6, fill=True))
            self.silk.append(rect(W / 2 - 2.0, 119.2, 4.0, 1.8, w=0.25))
            self.silk.append(circle(W / 2, 120.1, 0.45, fill=True))

        # Full-width thin line below bar
        self.silk.append(line(3.0, 121.6, W - 3.0, 121.6, w=0.15))

        # Brand name centered at bottom
        self.silk.append(text(W / 2, 125.6, brand, size=2.25 if W >= 95 else 2.05, weight="700", spacing=0.40))
        if W >= 95.0:
            self.silver.append(line(W / 2 - 17.2, 124.8, W / 2 - 13.9, 124.8, w=0.28))
            self.silver.append(line(W / 2 + 13.9, 124.8, W / 2 + 17.2, 124.8, w=0.28))

        # Left service code (Silver)
        self.silver.append(text(11.8, 124.8, serial_left, size=1.35 if W >= 95 else 1.20, anchor="start", weight="600", spacing=0.14))

        # Right barcode & module code
        if W >= 95.0:
            bc_x = W - 27.9
            for bw in [0.35, 0.2, 0.6, 0.2, 0.2, 0.5, 0.2, 0.35, 0.6, 0.2, 0.35, 0.2, 0.5, 0.2, 0.35, 0.6, 0.2, 0.4]:
                self.silk.append(rect(bc_x, 122.3, bw, 1.4, fill=True))
                bc_x += bw + 0.32
            self.silver.append(text(W - 27.9, 125.6, f"{cat_code}-{serial_right}", size=1.35, anchor="start", weight="600", spacing=0.14))
        else:
            self.silver.append(text(W - 11.5, 124.8, f"{cat_code}-{serial_right}", size=1.20, anchor="end", weight="600", spacing=0.12))

    def hazard_stripes(self, x, y, zw, zh, step=1.6, w=0.35, target=None):
        if target is None:
            target = self.silk
        d = -zh
        while d < zw:
            x1 = max(x, x + d)
            y1 = y + max(0, -d)
            x2 = min(x + zw, x + d + zh)
            y2 = y + min(zh, zw - d)
            if x2 > x1 and y2 > y1:
                target.append(line(x1, y1, x2, y2, w=w, cap="butt"))
            d += step

    # ======================== EXPORT METHODS ========================

    def save_layer_svg(self, path, elements, color="#000000"):
        svg = [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}mm" height="{self.h}mm" viewBox="0 0 {self.w} {self.h}">',
            '  <g id="layer">'
        ]
        for el in elements:
            svg.append("    " + el.replace("CURR", color))
        svg.append("  </g>")
        svg.append("</svg>")
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(svg))

    def save_edge_cuts_svg(self, path):
        svg = [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}mm" height="{self.h}mm" viewBox="0 0 {self.w} {self.h}">',
            f'  <rect x="0" y="0" width="{self.w}" height="{self.h}" fill="none" stroke="#000000" stroke-width="0.1"/>'
        ]
        for hx, hy, hr, _ in self.holes:
            svg.append(f'  <circle cx="{hx:.3f}" cy="{hy:.3f}" r="{hr:.3f}" fill="none" stroke="#000000" stroke-width="0.1"/>')
        svg.append("</svg>")
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(svg))

    def render_preview_group(self, x_offset=0.0, y_offset=0.0):
        bg = self.mask_theme["bg"]
        border = self.mask_theme["border"]
        fg_silver = self.silver_color
        fg_silk = self.silk_color
        hole_fill = self.mask_theme["hole"]
        hole_rim = self.mask_theme["hole_rim"]

        lines = [f'<g transform="translate({x_offset:.3f}, {y_offset:.3f})">']
        lines.append(f'  <rect x="0" y="0" width="{self.w}" height="{self.h}" rx="0.8" fill="{bg}" stroke="{border}" stroke-width="0.30"/>')
        lines.append('  <g class="silver_layer">')
        for el in self.silver:
            lines.append("    " + el.replace("CURR", fg_silver))
        lines.append("  </g>")
        lines.append('  <g class="silk_layer">')
        for el in self.silk:
            lines.append("    " + el.replace("CURR", fg_silk))
        lines.append("  </g>")
        lines.append('  <g class="holes_layer">')
        for hx, hy, hr, _ in self.holes:
            lines.append(f'    <circle cx="{hx:.3f}" cy="{hy:.3f}" r="{hr:.3f}" fill="{hole_fill}" stroke="{hole_rim}" stroke-width="0.18"/>')
        lines.append("  </g>")
        lines.append("</g>")
        return "\n".join(lines)

    def save_preview_svg(self, path):
        bg = self.mask_theme["bg"]
        fg_silver = self.silver_color
        fg_silk = self.silk_color
        hole_fill = self.mask_theme["hole"]
        hole_rim = self.mask_theme["hole_rim"]

        svg = [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}mm" height="{self.h}mm" viewBox="0 0 {self.w} {self.h}">',
            f'  <rect x="0" y="0" width="{self.w}" height="{self.h}" fill="{bg}"/>',
            '  <g id="silver_layer">'
        ]
        for el in self.silver:
            svg.append("    " + el.replace("CURR", fg_silver))
        svg.append("  </g>")
        svg.append('  <g id="silk_layer">')
        for el in self.silk:
            svg.append("    " + el.replace("CURR", fg_silk))
        svg.append("  </g>")
        svg.append('  <g id="holes_layer">')
        for hx, hy, hr, _ in self.holes:
            svg.append(f'    <circle cx="{hx:.3f}" cy="{hy:.3f}" r="{hr:.3f}" fill="{hole_fill}" stroke="{hole_rim}" stroke-width="0.18"/>')
        svg.append("  </g>")
        svg.append("</svg>")
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(svg))

    def export_all(self, out_dir, inkscape_bin=r"C:\Program Files\Inkscape\bin\inkscape.com"):
        os.makedirs(out_dir, exist_ok=True)
        silk_svg = os.path.join(out_dir, "F_SilkS.svg")
        silver_svg = os.path.join(out_dir, "F_Silver_Cu_Mask.svg")
        edge_svg = os.path.join(out_dir, "Edge_Cuts.svg")
        prev_svg = os.path.join(out_dir, "preview.svg")
        prev_png = os.path.join(out_dir, "preview.png")

        self.save_layer_svg(silk_svg, self.silk, "#000000")
        self.save_layer_svg(silver_svg, self.silver, "#000000")
        self.save_edge_cuts_svg(edge_svg)
        self.save_preview_svg(prev_svg)

        if os.path.exists(inkscape_bin):
            for svg_file in (silk_svg, silver_svg, prev_svg):
                subprocess.run([
                    inkscape_bin, svg_file,
                    "--export-text-to-path",
                    "--export-plain-svg",
                    f"--export-filename={svg_file}"
                ], check=True)
            subprocess.run([
                inkscape_bin, prev_svg,
                "--export-type=png",
                "--export-dpi=300",
                f"--export-filename={prev_png}"
            ], check=True)
        print(f"Exported panel ({self.category}, mask={self.mask_name}, finish={self.finish_name}) -> {out_dir}")
