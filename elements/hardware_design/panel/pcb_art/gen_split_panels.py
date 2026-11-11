"""Generate two-part front panel for Elements v0.4:
  1. EXCITER section   - 20 HP (101.4 x 128.5 mm), Matte Black solder mask, White silk, Silver HASL
  2. RESONATOR section - 14 HP ( 70.9 x 128.5 mm), Pure White solder mask, Black silk, Silver HASL
Plus a side-by-side combined preview showing how the two panels mate in the Eurorack rack.
"""
import math, os, re, random

HERE = os.path.dirname(os.path.abspath(__file__))
SPLIT_DIR = os.path.join(HERE, "split")
EXC_DIR = os.path.join(SPLIT_DIR, "exciter")
RES_DIR = os.path.join(SPLIT_DIR, "resonator")
os.makedirs(EXC_DIR, exist_ok=True)
os.makedirs(RES_DIR, exist_ok=True)

H = 128.5
W_EXC = 101.4   # 20 HP
W_RES = 70.9    # 14 HP
PT = 0.352778
OFF = (119.8766, 412.5205)
PX = 0.12321

FONT = "font-family:Bahnschrift;font-weight:600;font-stretch:semi-condensed;"

def f(v):
    return ("%.3f" % v).rstrip("0").rstrip(".")

# Read holes from original ElementsV04.svg
svg_raw = open(os.path.join(HERE, "..", "ElementsV04.svg"), encoding="utf8").read()
all_holes = []
for m in re.finditer(r'<circle cx="([\d.]+)" cy="([\d.]+)" r="([\d.]+)"', svg_raw):
    gx = (float(m.group(1)) - OFF[0]) * PT
    gy = (float(m.group(2)) - OFF[1]) * PT
    gr = float(m.group(3)) * PT
    all_holes.append((gx, gy, gr))

def kind(h):
    x, y, r = h
    pr = r / PT
    if abs(pr - 14.46) < .1: return "play"
    if abs(pr - 10.63) < .1: return "pot"
    if abs(pr - 9.213) < .1: return "jack"
    if abs(pr - 7.157) < .03: return "led"
    if abs(pr - 7.228) < .03: return "btn"
    return "mount"

class PanelBuilder:
    def __init__(self, w, h, prefix, is_white_mask=False):
        self.w = w
        self.h = h
        self.prefix = prefix
        self.is_white = is_white_mask
        self.silk = []
        self.silver = []
        self.holes = []

    def line(self, layer, x1, y1, x2, y2, w=0.2):
        layer.append('<path d="M%s %sL%s %s" fill="none" stroke-width="%s" stroke-linecap="butt"/>' % (f(x1), f(y1), f(x2), f(y2), w))

    def circ(self, layer, x, y, r, w=0.2, fill=False):
        if fill:
            layer.append('<circle cx="%s" cy="%s" r="%s" stroke="none" class="%s-fill"/>' % (f(x), f(y), f(r), "silver" if layer is self.silver else "silk"))
        else:
            layer.append('<circle cx="%s" cy="%s" r="%s" fill="none" stroke-width="%s"/>' % (f(x), f(y), f(r), w))

    def poly(self, layer, pts, w=0.2, closed=True, fill=False):
        d = "M" + "L".join("%s %s" % (f(a), f(b)) for a, b in pts) + ("Z" if closed else "")
        if fill:
            layer.append('<path d="%s" stroke="none" class="%s-fill"/>' % (d, "silver" if layer is self.silver else "silk"))
        else:
            layer.append('<path d="%s" fill="none" stroke-width="%s" stroke-linejoin="miter"/>' % (d, w))

    def arc(self, layer, cx, cy, r, a0, a1, w=0.25):
        def p(a):
            t = math.radians(a)
            return cx + r * math.sin(t), cy - r * math.cos(t)
        x0, y0 = p(a0); x1, y1 = p(a1)
        large = 1 if (a1 - a0) > 180 else 0
        layer.append('<path d="M%s %sA%s %s 0 %d 1 %s %s" fill="none" stroke-width="%s" stroke-linecap="butt"/>'
                     % (f(x0), f(y0), f(r), f(r), large, f(x1), f(y1), w))

    def dashed(self, layer, pts, on=0.5, off=0.85, w=0.3):
        segs = []
        for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
            L = math.hypot(x2 - x1, y2 - y1)
            ux, uy = (x2 - x1) / L, (y2 - y1) / L
            s = 0.0
            while s < L:
                e = min(s + on, L)
                segs.append("M%s %sL%s %s" % (f(x1 + ux * s), f(y1 + uy * s), f(x1 + ux * e), f(y1 + uy * e)))
                s += on + off
        layer.append('<path d="%s" fill="none" stroke-width="%s"/>' % ("".join(segs), w))

    def text(self, layer, s, x, y, size=2.9, anchor="middle", ls=0.28):
        cls = "%s-fill" % ("silver" if layer is self.silver else "silk")
        layer.append('<text x="%s" y="%s" style="%sfont-size:%s;letter-spacing:%s;text-anchor:%s" stroke="none" class="%s">%s</text>'
                     % (f(x), f(y), FONT, f(size), f(ls), anchor, cls, s))

    def chamfer_rect(self, cx, cy, w, h, c):
        x0, x1, y0, y1 = cx - w / 2, cx + w / 2, cy - h / 2, cy + h / 2
        return [(x0 + c, y0), (x1, y0), (x1, y1 - c), (x1 - c, y1), (x0, y1), (x0, y0 + c)]

    def tw(self, s, size=2.9, ls=0.28):
        return len(s) * (0.50 * size + ls)

    def label(self, s, cx, cy, style="A", size=2.9, ls=0.28, pad=3.2):
        base = cy + size * 0.36
        if style == "A":
            self.text(self.silk, s, cx, base, size, "middle", ls)
        elif style == "B":
            w = self.tw(s, size, ls) + pad
            self.poly(self.silver, self.chamfer_rect(cx, cy, w, 3.9, 1.0), 0.25)
            self.text(self.silver, s, cx + 0.14, base, size, "middle", ls)
        else: # style C
            w = self.tw(s, size, ls) + pad
            self.poly(self.silk, self.chamfer_rect(cx, cy, w, 3.9, 1.0), 0.2)
            self.text(self.silk, s, cx + 0.14, base, size, "middle", ls)

    def scale_ring(self, cx, cy, r1, r2, n=21, span=125):
        for i in range(n):
            a = -span + 2 * span * i / (n - 1)
            t = math.radians(a)
            mid = i == (n - 1) // 2
            end = i in (0, n - 1)
            ra = r1 - (0.8 if mid else 0)
            self.line(self.silk, cx + ra * math.sin(t), cy - ra * math.cos(t), cx + r2 * math.sin(t), cy - r2 * math.cos(t), 0.2 if (mid or end) else 0.15)
        self.arc(self.silver, cx, cy, r2 + 0.9, -span, span, 0.25)
        for a in (-span, span):
            t = math.radians(a)
            self.circ(self.silver, cx + (r2 + 0.9) * math.sin(t), cy - (r2 + 0.9) * math.cos(t), 0.55, fill=True)

    def hazard(self, x0, x1, y0, y1, pitch=2.4):
        xx = x0
        while xx < x1:
            a, b = xx, min(xx + pitch / 2, x1)
            pts = [(a, y1), (a + 3.0, y0), (b + 3.0, y0), (b, y1)]
            pts = [(min(max(px_, x0), x1), py_) for px_, py_ in pts]
            self.poly(self.silver, pts, fill=True)
            xx += pitch
        self.line(self.silver, x0, y0, x1, y0, 0.25)
        self.line(self.silver, x0, y1, x1, y1, 0.25)

    def doc(self, body, color):
        head = ('<svg xmlns="http://www.w3.org/2000/svg" width="%smm" height="%smm" viewBox="0 0 %s %s">'
                '<style>.%s-fill, .silk-fill, .silver-fill{fill:%s}</style>' % (self.w, self.h, self.w, self.h, self.prefix, color))
        return head + '<g stroke="%s" fill="none">' % color + "".join(body) + "</g></svg>"

    def edge_svg(self):
        head = ('<svg xmlns="http://www.w3.org/2000/svg" width="%smm" height="%smm" viewBox="0 0 %s %s">'
                % (self.w, self.h, self.w, self.h))
        out = [head + '<g stroke="#000000" fill="none" stroke-width="0.254">',
               '<rect x="0" y="0" width="%s" height="%s"/>' % (self.w, self.h)]
        for (x, y, r) in self.holes:
            out.append('<circle cx="%s" cy="%s" r="%s"/>' % (f(x), f(y), f(r)))
        out.append('</g></svg>')
        return "".join(out)

    def preview_body(self):
        mask_col = "#ffffff" if self.is_white else "#0c0c0e"
        silk_col = "#111113" if self.is_white else "#f4f4f0"
        silver_col = "#b9bec7"
        hole_fill = "#e0e0e0" if not self.is_white else "#cccccc"
        pfx = self.prefix

        holes_s = "".join('<circle cx="%s" cy="%s" r="%s" fill="%s" stroke="none"/>' % (f(x), f(y), f(r), hole_fill) for x, y, r in self.holes)
        body = (f'<g id="{pfx}_panel">'
                + f'<rect width="{self.w}" height="{self.h}" fill="{mask_col}"/>'
                + f'<g id="{pfx}_silver" stroke="{silver_col}" fill="none" style="fill:none;">'
                + f'<style>#{pfx}_silver .{pfx}-fill, #{pfx}_silver .silver-fill{{fill:{silver_col}!important}}</style>'
                + "".join(self.silver) + "</g>"
                + f'<g id="{pfx}_silk" stroke="{silk_col}" fill="none" style="fill:none;">'
                + f'<style>#{pfx}_silk .{pfx}-fill, #{pfx}_silk .silk-fill{{fill:{silk_col}!important}}</style>'
                + "".join(self.silk) + "</g>"
                + holes_s + "</g>")
        return body

    def preview_svg(self):
        head = f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}mm" height="{self.h}mm" viewBox="0 0 {self.w} {self.h}">'
        return head + self.preview_body() + "</svg>"

# ==============================================================================
# BUILD EXCITER PANEL (20 HP) - MATTE BLACK SOLDER MASK
# ==============================================================================
exc = PanelBuilder(W_EXC, H, "exc", is_white_mask=False)

for h in all_holes:
    gx, gy, gr = h
    if gx < W_EXC:
        if kind(h) == "mount":
            if gx < 20:
                exc.holes.append((gx, gy, gr))
        else:
            exc.holes.append((gx, gy, gr))

# Standard 20HP mounting holes at right edge (x = 101.4 - 7.5 = 93.9 mm)
exc.holes.append((93.90, 2.99, 1.6))
exc.holes.append((93.90, 125.51, 1.6))

# Header
exc.text(exc.silk, "ELEMENTS", 16.0, 6.9, 5.4, "start", 1.5)
exc.text(exc.silver, "EXCITER // 20HP", 95.0, 6.6, 2.1, "end", 0.55)
exc.line(exc.silver, 54.0, 4.6, 69.0, 4.6, 0.3)
exc.line(exc.silver, 54.0, 5.5, 64.0, 5.5, 0.2)
exc.line(exc.silver, 3.3, 8.2, 98.1, 8.2, 0.25)
exc.line(exc.silver, 3.3, 10.9, 98.1, 10.9, 0.25)
x = 5.0
while x < 97.0:
    exc.poly(exc.silver, [(x, 8.95), (x + 0.9, 9.55), (x, 10.15)], 0.22, closed=False)
    x += 2.4

# Knobs
for h in exc.holes:
    gx, gy, gr = h
    k = kind(h)
    if k == "pot":
        if abs(gy / PX - 172) < 8:
            exc.scale_ring(gx, gy, 7.0, 8.3)
        elif abs(gy / PX - 392) < 8:
            exc.scale_ring(gx, gy, 7.8, 9.2, n=23)
            exc.circ(exc.silver, gx, gy, 6.2, 0.2)
        elif abs(gy / PX - 612) < 8:
            exc.circ(exc.silver, gx, gy, 5.4, 0.2)

# Top row connector (CONTOUR -> BOW -> BLOW -> STRIKE)
exc_tops = sorted([h[0] for h in exc.holes if kind(h) == "pot" and abs(h[1] / PX - 172) < 8])
for a, b in zip(exc_tops[:3], exc_tops[1:4]):
    exc.dashed(exc.silver, [(a + 9.9, 21.23), (b - 9.9, 21.23)], 0.45, 0.8, 0.3)

# Top labels
exc.label("CONTOUR", 16.73, 31.6)
exc.label("BOW", 40.51, 31.6)
exc.label("BLOW", 64.32, 31.6, "B")
exc.label("STRIKE", 88.17, 31.6, "C")

# CONTOUR polarity icons
cxn = 16.73
for dx_, kindname in ((-8.8, "sharp"), (8.8, "round")):
    ix, iy = cxn + dx_ * 1.09, 29.2
    exc.circ(exc.silk, ix, iy, 1.5, 0.18)
    if kindname == "sharp":
        exc.poly(exc.silk, [(ix - .8, iy + .6), (ix + .5, iy - .7), (ix + .5, iy + .6)], 0.18, closed=False)
    else:
        exc.silk.append('<path d="M%s %sC%s %s %s %s %s %s" fill="none" stroke-width="0.18"/>' % (f(ix - .85), f(iy + .55), f(ix - .85), f(iy - .95), f(ix + .85), f(iy - .95), f(ix + .85), f(iy + .55)))

# Big pot labels
exc.label("FLOW", 47.81, 57.0, "B")
exc.label("MALLET", 80.83, 57.0, "C")

# Mid pot labels
exc.label("TIMBRE", 40.51, 86.0)
exc.label("TIMBRE", 64.32, 86.0, "B")
exc.label("TIMBRE", 88.17, 86.0, "C")

# PLAY button
pl = [h for h in exc.holes if kind(h) == "play"][0]
exc.circ(exc.silver, pl[0], pl[1], 7.0, 0.3)
for i in range(36):
    a = 360 * i / 36; t = math.radians(a)
    exc.line(exc.silk, pl[0] + 8.2 * math.sin(t), pl[1] - 8.2 * math.cos(t), pl[0] + 9.2 * math.sin(t), pl[1] - 9.2 * math.cos(t), 0.2)
exc.text(exc.silk, "PLAY", 227 * PX, pl[1] + 1.0, 2.9, "start", 0.28)

# MODEL button & LED
btn_l = [h for h in exc.holes if kind(h) == "btn"][0]
led_l = [h for h in exc.holes if kind(h) == "led"][0]
exc.circ(exc.silver, led_l[0], led_l[1], led_l[2] + 1.0, 0.3)
exc.circ(exc.silk, led_l[0], led_l[1], led_l[2] + 1.9, 0.15)
exc.circ(exc.silk, btn_l[0], btn_l[1], btn_l[2] + 1.1, 0.2)
exc.text(exc.silk, "MODEL", btn_l[0] + 0.12, btn_l[1] + btn_l[2] + 1.1 + 2.7, 2.0, "middle", 0.3)
exc.poly(exc.silver, [(btn_l[0] - 4.9, btn_l[1] - 1.0), (btn_l[0] - 6.0, btn_l[1]), (btn_l[0] - 4.9, btn_l[1] + 1.0)], 0.28, closed=False)

# Left column jacks
for h in exc.holes:
    if kind(h) == "jack" and h[0] < 30:
        if h[1] / PX > 880:
            exc.circ(exc.silver, h[0], h[1], h[2] + 1.5, 0.35)
        else:
            exc.circ(exc.silk, h[0], h[1], h[2] + 1.15, 0.15)

exc.label("V/OCT", 87 * PX, 467 * PX)
exc.label("FM", 185 * PX, 467 * PX)
exc.label("GATE", 87 * PX, 594 * PX)
exc.label("STRENGTH", 185 * PX, 594 * PX)
exc.label("EXT IN", 87 * PX, 720 * PX, "B", 2.4, 0.1, 2.4)
exc.label("EXT IN", 185 * PX, 720 * PX, "C", 2.4, 0.1, 2.4)
for cxp, nm in ((87, "OUT L"), (185, "OUT R")):
    cx = cxp * PX
    exc.poly(exc.silver, exc.chamfer_rect(cx, 109.4, 10.6, 16.4, 1.6), 0.3)
    exc.text(exc.silk, nm, cx, 104.3, 2.4, "middle", 0.25)

# Attenuverter columns (Exciter)
att_l = sorted([h for h in exc.holes if kind(h) == "jack" and h[0] > 25 and abs(h[1] / PX - 775) < 8], key=lambda h: h[0])
cvj_l = sorted([h for h in exc.holes if kind(h) == "jack" and h[0] > 25 and abs(h[1] / PX - 901) < 8], key=lambda h: h[0])
for (x, y, r) in att_l:
    exc.line(exc.silk, x - 3.9, 90.5, x - 2.5, 90.5, 0.18)
    exc.line(exc.silk, x + 2.5, 90.5, x + 3.9, 90.5, 0.18)
    exc.line(exc.silk, x + 3.2, 89.8, x + 3.2, 91.2, 0.18)
    exc.line(exc.silk, x, 89.4, x, 91.4, 0.18)
    exc.circ(exc.silk, x, y, r + 1.15, 0.15)
for (x, y, r) in cvj_l:
    exc.circ(exc.silk, x, y, r + 1.15, 0.15)
for a, c in zip(att_l, cvj_l):
    exc.dashed(exc.silver, [(a[0], a[1] + a[2] + 2.0), (c[0], c[1] - c[2] - 2.0)], 0.5, 0.85, 0.3)

def exc_route(pts):
    exc.dashed(exc.silver, pts, 0.5, 0.85, 0.3)
    for p in (pts[0], pts[-1]):
        exc.circ(exc.silver, p[0], p[1], 0.55, fill=True)

exc_route([(47.81, 59.9), (47.81, 89.0)])
exc_route([(80.83, 59.9), (80.83, 70.5), (77.34, 74.5), (77.34, 89.0)])

# Right edge interface / bus connector (mates with Resonator)
exc.line(exc.silver, 98.1, 13.0, 98.1, 114.0, 0.25)
for py_node in (25.0, 48.0, 75.0, 95.0, 111.0):
    exc.poly(exc.silver, [(98.1, py_node - 1.2), (99.8, py_node), (98.1, py_node + 1.2)], fill=True)
    exc.circ(exc.silver, 96.0, py_node, 0.6, fill=True)
    exc.line(exc.silver, 96.0, py_node, 98.1, py_node, 0.2)

# Footer
BY = 119.3
exc.hazard(3.3, 35.0, BY - 1.5, BY + 1.5)
exc.line(exc.silver, 38.0, BY, 98.1, BY, 0.35)
exc.text(exc.silk, "DECØY DEVICES", 50.7, 125.6, 2.6, "middle", 1.3)
exc.text(exc.silk, "DD-EL04-EXC // 20HP", 38.0, 121.2, 1.3, "start", 0.4)

for rx, ry in ((3.3, 13.0), (3.3, 114.0)):
    exc.line(exc.silk, rx - 1.2, ry, rx + 1.2, ry, 0.15)
    exc.line(exc.silk, rx, ry - 1.2, rx, ry + 1.2, 0.15)

# ==============================================================================
# BUILD RESONATOR PANEL (14 HP) - PURE WHITE SOLDER MASK!
# ==============================================================================
res = PanelBuilder(W_RES, H, "res", is_white_mask=True)

for h in all_holes:
    gx, gy, gr = h
    if gx >= W_EXC:
        if kind(h) == "mount":
            if gx > 150:
                res.holes.append((gx - W_EXC, gy, gr))
        else:
            res.holes.append((gx - W_EXC, gy, gr))

# Standard 14HP mounting holes at left edge (x = 7.50 mm)
res.holes.append((7.50, 2.99, 1.6))
res.holes.append((7.50, 125.51, 1.6))

# Header (compacted to prevent collision on 14HP width)
res.text(res.silk, "RESONATOR", 7.5, 6.9, 4.2, "start", 0.8)
res.text(res.silver, "7-MODEL ENGINE // 14HP", 66.5, 6.6, 1.7, "end", 0.35)
res.line(res.silver, 3.3, 8.2, 67.6, 8.2, 0.25)
res.line(res.silver, 3.3, 10.9, 67.6, 10.9, 0.25)
x = 5.0
while x < 66.5:
    res.poly(res.silver, [(x, 8.95), (x + 0.9, 9.55), (x, 10.15)], 0.22, closed=False)
    x += 2.4

# Knobs
for h in res.holes:
    lx, ly, lr = h
    k = kind(h)
    if k == "pot":
        if abs(ly / PX - 172) < 8:
            res.scale_ring(lx, ly, 7.0, 8.3)
        elif abs(ly / PX - 392) < 8:
            res.scale_ring(lx, ly, 7.8, 9.2, n=23)
            res.circ(res.silver, lx, ly, 6.2, 0.2)
        elif abs(ly / PX - 612) < 8:
            res.circ(res.silver, lx, ly, 5.4, 0.2)

# Top row labels (local X = glob_X - 101.4)
res.label("COARSE", 111.98 - W_EXC, 31.6)
res.label("FINE", 135.79 - W_EXC, 31.6)
res.label("FM", 159.61 - W_EXC, 31.6)

# FM polarity icons
fmx = 159.61 - W_EXC
for dx_, sym in ((-8.8, "-"), (8.8, "+")):
    ix, iy = fmx + dx_ * 1.09, 29.2
    res.circ(res.silk, ix, iy, 1.5, 0.18)
    res.line(res.silk, ix - .7, iy, ix + .7, iy, 0.18)
    if sym == "+":
        res.line(res.silk, ix, iy - .7, ix, iy + .7, 0.18)

# Big pot labels
res.label("GEOMETRY", 119.28 - W_EXC, 57.0)
res.label("BRIGHTNESS", 152.30 - W_EXC, 57.0)

# Mid pot labels
res.label("DAMPING", 111.98 - W_EXC, 86.0)
res.label("POSITION", 135.79 - W_EXC, 86.0)
res.label("SPACE", 159.61 - W_EXC, 86.0)

# MODEL button & LED
btn_r = [h for h in res.holes if kind(h) == "btn"][0]
led_r = [h for h in res.holes if kind(h) == "led"][0]
res.circ(res.silver, led_r[0], led_r[1], led_r[2] + 1.0, 0.3)
res.circ(res.silk, led_r[0], led_r[1], led_r[2] + 1.9, 0.15)
res.circ(res.silk, btn_r[0], btn_r[1], btn_r[2] + 1.1, 0.2)
res.text(res.silk, "MODEL", btn_r[0] + 0.12, btn_r[1] + btn_r[2] + 1.1 + 2.7, 2.0, "middle", 0.3)
res.poly(res.silver, [(btn_r[0] + 4.9, btn_r[1] - 1.0), (btn_r[0] + 6.0, btn_r[1]), (btn_r[0] + 4.9, btn_r[1] + 1.0)], 0.28, closed=False)

# Attenuverter columns (Resonator)
att_r = sorted([h for h in res.holes if kind(h) == "jack" and abs(h[1] / PX - 775) < 8], key=lambda h: h[0])
cvj_r = sorted([h for h in res.holes if kind(h) == "jack" and abs(h[1] / PX - 901) < 8], key=lambda h: h[0])
for (x, y, r) in att_r:
    res.line(res.silk, x - 3.9, 90.5, x - 2.5, 90.5, 0.18)
    res.line(res.silk, x + 2.5, 90.5, x + 3.9, 90.5, 0.18)
    res.line(res.silk, x + 3.2, 89.8, x + 3.2, 91.2, 0.18)
    res.line(res.silk, x, 89.4, x, 91.4, 0.18)
    res.circ(res.silk, x, y, r + 1.15, 0.15)
for (x, y, r) in cvj_r:
    res.circ(res.silk, x, y, r + 1.15, 0.15)
for a, c in zip(att_r, cvj_r):
    res.dashed(res.silver, [(a[0], a[1] + a[2] + 2.0), (c[0], c[1] - c[2] - 2.0)], 0.5, 0.85, 0.3)

def res_route(pts):
    res.dashed(res.silver, pts, 0.5, 0.85, 0.3)
    for p in (pts[0], pts[-1]):
        res.circ(res.silver, p[0], p[1], 0.55, fill=True)

geom_x = 119.28 - W_EXC
damp_x = 109.79 - W_EXC
bright_x = 152.30 - W_EXC
space_x = 148.81 - W_EXC
res_route([(geom_x, 59.9), (geom_x, 70.5), (damp_x, 74.5), (damp_x, 89.0)])
res_route([(bright_x, 59.9), (bright_x, 89.0)])

# Left edge interface / bus connector (mates with Exciter)
res.line(res.silver, 2.5, 13.0, 2.5, 114.0, 0.25)
for py_node in (25.0, 48.0, 75.0, 95.0, 111.0):
    res.poly(res.silver, [(2.5, py_node - 1.2), (1.0, py_node), (2.5, py_node + 1.2)], fill=True)
    res.circ(res.silver, 4.6, py_node, 0.6, fill=True)
    res.line(res.silver, 2.5, py_node, 4.6, py_node, 0.2)

# Footer
res.hazard(38.0, 67.6, BY - 1.5, BY + 1.5)
res.line(res.silver, 2.5, BY, 34.0, BY, 0.35)

# Barcode on Resonator (black silk, positioned safely between x=14 and 32)
rnd = random.Random(404)
bx = 14.0
while bx < 32.0:
    bw = rnd.choice((0.3, 0.3, 0.5, 0.8))
    res.poly(res.silk, [(bx, 121.6), (bx + bw, 121.6), (bx + bw, 125.4), (bx, 125.4)], fill=True)
    bx += bw + rnd.choice((0.3, 0.4, 0.6))
res.text(res.silk, "ELM-04-H743", 23.0, 127.0, 1.1, "middle", 0.3)
res.text(res.silk, "DD-EL04-RES // 14HP", 50.0, 125.6, 1.4, "middle", 0.5)

for rx, ry in ((67.6, 13.0), (67.6, 114.0)):
    res.line(res.silk, rx - 1.2, ry, rx + 1.2, ry, 0.15)
    res.line(res.silk, rx, ry - 1.2, rx, ry + 1.2, 0.15)

# ==============================================================================
# WRITE FILES
# ==============================================================================
def write_panel(builder, out_dir, prefix):
    open(os.path.join(out_dir, f"{prefix}_F_SilkS.svg"), "w", encoding="utf8").write(
        builder.doc(builder.silk, "#000000").replace('class="silk-fill"', 'fill="#000000"').replace('class="silver-fill"', 'fill="#000000"')
    )
    open(os.path.join(out_dir, f"{prefix}_F_Silver_Cu_Mask.svg"), "w", encoding="utf8").write(
        builder.doc(builder.silver, "#000000").replace('class="silk-fill"', 'fill="#000000"').replace('class="silver-fill"', 'fill="#000000"')
    )
    open(os.path.join(out_dir, f"{prefix}_Edge_Cuts.svg"), "w", encoding="utf8").write(
        builder.edge_svg()
    )
    open(os.path.join(out_dir, f"{prefix}_preview.svg"), "w", encoding="utf8").write(
        builder.preview_svg()
    )

write_panel(exc, EXC_DIR, "Exciter")
write_panel(res, RES_DIR, "Resonator")

# Combined Side-by-Side Rack Preview (34 HP total)
GAP = 0.3 # 0.3 mm Eurorack clearance gap
W_TOTAL = W_EXC + GAP + W_RES
side_by_side = (
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{W_TOTAL}mm" height="{H}mm" viewBox="0 0 {W_TOTAL} {H}">'
    f'<rect width="{W_TOTAL}" height="{H}" fill="#141416"/>'
    f'<g transform="translate(0, 0)">{exc.preview_body()}</g>'
    f'<g transform="translate({W_EXC + GAP}, 0)">{res.preview_body()}</g>'
    '</svg>'
)
open(os.path.join(SPLIT_DIR, "split_panels_preview.svg"), "w", encoding="utf8").write(side_by_side)
print("Exciter holes:", len(exc.holes), "silk:", len(exc.silk), "silver:", len(exc.silver))
print("Resonator holes:", len(res.holes), "silk:", len(res.silk), "silver:", len(res.silver))
