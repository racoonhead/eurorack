"""Elements v0.4 front-panel artwork for PCB fabrication.

Generates (all in mm, origin = top-left of the 172.5 x 128.5 mm panel):
  F_SilkS.svg      white silkscreen
  F_Silver_Cu_Mask.svg  HASL silver = copper shapes + solder-mask openings (import to F.Cu AND F.Mask)
  Edge_Cuts.svg    outline + all drilled holes
  preview.svg      all layers composited (black mask / white silk / silver HASL)
Run:  py gen_panel.py   (then inkscape converts text to paths, see build.ps1)
"""
import math, re, os

HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 172.5, 128.5
PT = 0.352778                      # pt -> mm
OFF = (119.8766, 412.5205)         # panel origin in ElementsV04.svg (pt)
PX = 0.12321                       # 1400px preview -> mm (px of the old artwork)

FONT = "font-family:Bahnschrift;font-weight:600;font-stretch:semi-condensed;"

silk, gold = [], []


def f(v):
    return ("%.3f" % v).rstrip("0").rstrip(".")


# ---------------------------------------------------------------- holes
svg = open(os.path.join(HERE, "..", "ElementsV04.svg"), encoding="utf8").read()
holes = []
for m in re.finditer(r'<circle cx="([\d.]+)" cy="([\d.]+)" r="([\d.]+)"', svg):
    x = (float(m.group(1)) - OFF[0]) * PT
    y = (float(m.group(2)) - OFF[1]) * PT
    r = float(m.group(3)) * PT
    holes.append((x, y, r))


def kind(h):
    x, y, r = h
    pr = r / PT
    if abs(pr - 14.46) < .1: return "play"
    if abs(pr - 10.63) < .1: return "pot"
    if abs(pr - 9.213) < .1: return "jack"
    if abs(pr - 7.157) < .03: return "led"
    if abs(pr - 7.228) < .03: return "btn"
    return "mount"


# ---------------------------------------------------------------- primitives
def line(layer, x1, y1, x2, y2, w=0.2):
    layer.append('<path d="M%s %sL%s %s" fill="none" stroke-width="%s" stroke-linecap="butt"/>' % (f(x1), f(y1), f(x2), f(y2), w))


def circ(layer, x, y, r, w=0.2, fill=False):
    if fill:
        layer.append('<circle cx="%s" cy="%s" r="%s" stroke="none" class="fill"/>' % (f(x), f(y), f(r)))
    else:
        layer.append('<circle cx="%s" cy="%s" r="%s" fill="none" stroke-width="%s"/>' % (f(x), f(y), f(r), w))


def poly(layer, pts, w=0.2, closed=True, fill=False):
    d = "M" + "L".join("%s %s" % (f(a), f(b)) for a, b in pts) + ("Z" if closed else "")
    if fill:
        layer.append('<path d="%s" stroke="none" class="fill"/>' % d)
    else:
        layer.append('<path d="%s" fill="none" stroke-width="%s" stroke-linejoin="miter"/>' % (d, w))


def arc(layer, cx, cy, r, a0, a1, w=0.25):
    """angles in degrees, 0 = up, clockwise positive"""
    def p(a):
        t = math.radians(a)
        return cx + r * math.sin(t), cy - r * math.cos(t)
    x0, y0 = p(a0); x1, y1 = p(a1)
    large = 1 if (a1 - a0) > 180 else 0
    layer.append('<path d="M%s %sA%s %s 0 %d 1 %s %s" fill="none" stroke-width="%s" stroke-linecap="butt"/>'
                 % (f(x0), f(y0), f(r), f(r), large, f(x1), f(y1), w))


def dashed(layer, pts, on=0.5, off=0.9, w=0.35):
    """explicit dashes (KiCad's SVG import ignores stroke-dasharray)"""
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


def text(layer, s, x, y, size=2.9, anchor="middle", ls=0.28):
    layer.append('<text x="%s" y="%s" style="%sfont-size:%s;letter-spacing:%s;text-anchor:%s" stroke="none" class="fill">%s</text>'
                 % (f(x), f(y), FONT, f(size), f(ls), anchor, s))


def chamfer_rect(cx, cy, w, h, c):
    x0, x1, y0, y1 = cx - w / 2, cx + w / 2, cy - h / 2, cy + h / 2
    return [(x0 + c, y0), (x1, y0), (x1, y1 - c), (x1 - c, y1), (x0, y1), (x0, y0 + c)]


def tw(s, size=2.9, ls=0.28):
    return len(s) * (0.50 * size + ls)


def label(s, px, py, style="A", size=2.9, ls=0.28, pad=3.2):
    """style A: plain white / B: gold framed (red in old art) / C: white framed (teal in old art)"""
    cx, cy = px * PX, py * PX
    base = cy + size * 0.36
    if style == "A":
        text(silk, s, cx, base, size, "middle", ls)
    elif style == "B":
        w = tw(s, size, ls) + pad
        poly(gold, chamfer_rect(cx, cy, w, 3.9, 1.0), 0.25)
        text(gold, s, cx + 0.14, base, size, "middle", ls)
    else:
        w = tw(s, size, ls) + pad
        poly(silk, chamfer_rect(cx, cy, w, 3.9, 1.0), 0.2)
        text(silk, s, cx + 0.14, base, size, "middle", ls)
    return cx, cy


def scale_ring(cx, cy, r1, r2, n=21, span=125):
    for i in range(n):
        a = -span + 2 * span * i / (n - 1)
        t = math.radians(a)
        mid = i == (n - 1) // 2
        end = i in (0, n - 1)
        ra = r1 - (0.8 if mid else 0)
        line(silk, cx + ra * math.sin(t), cy - ra * math.cos(t), cx + r2 * math.sin(t), cy - r2 * math.cos(t), 0.2 if (mid or end) else 0.15)
    arc(gold, cx, cy, r2 + 0.9, -span, span, 0.25)
    for a in (-span, span):
        t = math.radians(a)
        circ(gold, cx + (r2 + 0.9) * math.sin(t), cy - (r2 + 0.9) * math.cos(t), 0.55, fill=True)


# ---------------------------------------------------------------- layout
tops = [h for h in holes if kind(h) == "pot" and abs(h[1] / PX - 172) < 8]
bigs = [h for h in holes if kind(h) == "pot" and abs(h[1] / PX - 392) < 8]
mids = [h for h in holes if kind(h) == "pot" and abs(h[1] / PX - 612) < 8]

import random
# frame / header ------------------------------------------------------------
text(silk, "ELEMENTS", 17.0, 6.9, 5.4, "start", 1.5)
text(gold, "MODAL SYNTHESIZER // V0.4", 155.0, 6.6, 2.1, "end", 0.55)
line(gold, 54.0, 4.6, 69.0, 4.6, 0.3)          # glitch tear through the title
line(gold, 54.0, 5.5, 64.0, 5.5, 0.2)
rnd2 = random.Random(77)
bx = 72.0
while bx < 108.0:
    bw = rnd2.choice((1.2, 2.4, 3.6, 0.6)); bh = rnd2.choice((0.5, 0.8, 1.2))
    poly(gold, [(bx, 6.4), (bx + bw, 6.4), (bx + bw, 6.4 - bh), (bx, 6.4 - bh)], fill=True)
    bx += bw + 0.8
line(gold, 3.3, 8.2, 169.2, 8.2, 0.25)
line(gold, 3.3, 10.9, 169.2, 10.9, 0.25)
x = 5.0
while x < 168:
    poly(gold, [(x, 8.95), (x + 0.9, 9.55), (x, 10.15)], 0.22, closed=False)
    x += 2.4

# divider --------------------------------------------------------------------
DX = 811 * PX
for s in (-0.8, 0.8):
    line(gold, DX + s, 13.0, DX + s, 55.0, 0.2)
    line(gold, DX + s, 67.0, DX + s, 115.0, 0.2)
for yy in list(range(15, 55, 7)) + list(range(70, 115, 7)):
    poly(gold, [(DX, yy - 0.8), (DX + 0.8, yy), (DX, yy + 0.8), (DX - 0.8, yy)], fill=True)
ey = 61.0
poly(gold, [(DX + 4.2 * math.cos(math.radians(a)), ey + 4.2 * math.sin(math.radians(a))) for a in range(0, 360, 60)], 0.3)
circ(silk, DX, ey, 2.3, 0.2)
circ(gold, DX, ey, 0.8, fill=True)
for a in range(0, 360, 60):
    t = math.radians(a)
    line(silk, DX + 2.3 * math.cos(t), ey + 2.3 * math.sin(t), DX + 3.5 * math.cos(t), ey + 3.5 * math.sin(t), 0.15)

for sgn in (-1, 1):
    pts = [(DX + sgn * 4.2, ey), (DX + sgn * 8.0, ey), (DX + sgn * 10.5, ey + 2.5), (DX + sgn * 10.5, ey + 5.0)]
    poly(gold, pts, 0.2, closed=False)
    circ(gold, pts[-1][0], pts[-1][1], 0.6, 0.2)
    pts = [(DX + sgn * 4.2, ey - 1.5), (DX + sgn * 6.5, ey - 1.5), (DX + sgn * 8.0, ey - 3.0), (DX + sgn * 8.0, ey - 5.0)]
    poly(gold, pts, 0.2, closed=False)
    circ(gold, pts[-1][0], pts[-1][1], 0.6, fill=True)
# registration marks
for rx, ry in ((3.3, 13.0), (169.2, 13.0), (3.3, 114.0), (169.2, 114.0)):
    line(silk, rx - 1.2, ry, rx + 1.2, ry, 0.15); line(silk, rx, ry - 1.2, rx, ry + 1.2, 0.15)
# bottom bar + footer ---------------------------------------------------------
BY = 119.3
poly(gold, [(42.0, BY - 0.35), (130.5, BY - 0.35), (130.5, BY + 0.35), (42.0, BY + 0.35)], fill=True)
def hazard(x0, x1, y0=BY - 1.5, y1=BY + 1.5, pitch=2.4):
    xx = x0
    while xx < x1:
        a, b = xx, min(xx + pitch / 2, x1)
        # parallelogram clipped to [x0, x1]
        pts = [(a, y1), (a + 3.0, y0), (b + 3.0, y0), (b, y1)]
        pts = [(min(max(px_, x0), x1), py_) for px_, py_ in pts]
        poly(gold, pts, fill=True)
        xx += pitch
hazard(3.3, 38.0); hazard(134.5, 169.2)
line(gold, 3.3, BY - 1.5, 38.0, BY - 1.5, 0.25); line(gold, 3.3, BY + 1.5, 38.0, BY + 1.5, 0.25)
line(gold, 134.5, BY - 1.5, 169.2, BY - 1.5, 0.25); line(gold, 134.5, BY + 1.5, 169.2, BY + 1.5, 0.25)
# barcode (deterministic)
import random
rnd = random.Random(404)
bx = 140.0
while bx < 158.0:
    bw = rnd.choice((0.3, 0.3, 0.5, 0.8))
    poly(silk, [(bx, 121.6), (bx + bw, 121.6), (bx + bw, 125.4), (bx, 125.4)], fill=True)
    bx += bw + rnd.choice((0.3, 0.4, 0.6))
text(silk, "ELM-04-H743", 149.0, 127.0, 1.1, "middle", 0.3)
text(silk, "DECØY DEVICES", 86.25, 125.6, 2.6, "middle", 1.3)
text(silk, "DD-EL04 // REV 0.4", 16.0, 125.0, 1.5, "start", 0.5)

# top row (exciter knobs) -----------------------------------------------------
for (x, y, r) in tops:
    scale_ring(x, y, 7.0, 8.3)
xs = sorted(h[0] for h in tops)
for a, b in zip(xs[:3], xs[1:4]):               # CONTOUR-BOW-BLOW-STRIKE group link
    dashed(gold, [(a + 9.9, tops[0][1]), (b - 9.9, tops[0][1])], 0.45, 0.8, 0.3)
label("CONTOUR", 136, 257); label("BOW", 329, 257); label("BLOW", 522, 257, "B"); label("STRIKE", 715, 257, "C")
label("COARSE", 909, 257); label("FINE", 1102, 257); label("FM", 1295, 257)

# CONTOUR / FM polarity icons
cxn, cyn = 136 * PX, 172 * PX
for dx_, kindname in ((-8.8, "sharp"), (8.8, "round")):
    ix, iy = cxn + dx_ * 1.09, 29.2
    circ(silk, ix, iy, 1.5, 0.18)
    if kindname == "sharp":      # sharp attack: straight ramp up, vertical drop
        poly(silk, [(ix - .8, iy + .6), (ix + .5, iy - .7), (ix + .5, iy + .6)], 0.18, closed=False)
    else:                        # round attack: smooth half-sine hump
        silk.append('<path d="M%s %sC%s %s %s %s %s %s" fill="none" stroke-width="0.18"/>' % (f(ix - .85), f(iy + .55), f(ix - .85), f(iy - .95), f(ix + .85), f(iy - .95), f(ix + .85), f(iy + .55)))
fmx = 1295 * PX
for dx_, sym in ((-8.8, "-"), (8.8, "+")):
    ix, iy = fmx + dx_ * 1.09, 29.2
    circ(silk, ix, iy, 1.5, 0.18)
    line(silk, ix - .7, iy, ix + .7, iy, 0.18)
    if sym == "+":
        line(silk, ix, iy - .7, ix, iy + .7, 0.18)

# big knobs --------------------------------------------------------------------
for (x, y, r) in bigs:
    scale_ring(x, y, 7.8, 9.2, n=23)
    circ(gold, x, y, 6.2, 0.2)
label("FLOW", 388, 463, "B"); label("MALLET", 656, 463, "C")
label("GEOMETRY", 968, 463); label("BRIGHTNESS", 1236, 463)

# mid row pots -------------------------------------------------------------------
label("TIMBRE", 329, 698); label("TIMBRE", 522, 698, "B"); label("TIMBRE", 715, 698, "C")
label("DAMPING", 909, 698); label("POSITION", 1102, 698); label("SPACE", 1295, 698)
for (x, y, r) in mids:
    circ(gold, x, y, 5.4, 0.2)

# attenuverter columns -----------------------------------------------------------
att = sorted([h for h in holes if kind(h) == "jack" and h[0] > 230 * PX * 0 + 25 and abs(h[1] / PX - 775) < 8], key=lambda h: h[0])
cvj = sorted([h for h in holes if kind(h) == "jack" and h[0] > 25 and abs(h[1] / PX - 901) < 8], key=lambda h: h[0])
for (x, y, r) in att:
    if x < 30: continue
    line(silk, x - 3.9, 90.5, x - 2.5, 90.5, 0.18)
    line(silk, x + 2.5, 90.5, x + 3.9, 90.5, 0.18)
    line(silk, x + 3.2, 89.8, x + 3.2, 91.2, 0.18)
    line(silk, x, 89.4, x, 91.4, 0.18)
    circ(silk, x, y, r + 1.15, 0.15)
for (x, y, r) in cvj:
    if x < 30: continue
    circ(silk, x, y, r + 1.15, 0.15)
for a in att:
    for c in cvj:
        if abs(a[0] - c[0]) < 1 and a[0] > 30:
            dashed(gold, [(a[0], a[1] + a[2] + 2.0), (c[0], c[1] - c[2] - 2.0)], 0.5, 0.85, 0.3)

# exciter routing lines (gold dashed), routed around the two model buttons -------------
def route(pts):
    dashed(gold, pts, 0.5, 0.85, 0.3)
    for p in (pts[0], pts[-1]):
        circ(gold, p[0], p[1], 0.55, fill=True)

route([(417 * PX, 59.9), (417 * PX, 89.0)])
route([(84.0, 59.9), (84.0, 70.5), (628 * PX, 74.5), (628 * PX, 89.0)])
route([(115.3, 59.9), (115.3, 70.5), (997 * PX, 74.5), (997 * PX, 89.0)])
route([(1207 * PX, 59.9), (1207 * PX, 89.0)])

# left column jacks ------------------------------------------------------------------
left = [h for h in holes if kind(h) == "jack" and h[0] < 30]
for (x, y, r) in left:
    pyp = y / PX
    if pyp > 880:      # OUT L / OUT R : gold ring
        circ(gold, x, y, r + 1.5, 0.35)
    else:
        circ(silk, x, y, r + 1.15, 0.15)
label("V/OCT", 87, 467); label("FM", 185, 467)
label("GATE", 87, 594); label("STRENGTH", 185, 594)
label("EXT IN", 87, 720, "B", 2.4, 0.1, 2.4); label("EXT IN", 185, 720, "C", 2.4, 0.1, 2.4)
for cxp, nm in ((87, "OUT L"), (185, "OUT R")):
    cx = cxp * PX
    poly(gold, chamfer_rect(cx, 109.4, 10.6, 16.4, 1.6), 0.3)
    text(silk, nm, cx, 104.3, 2.4, "middle", 0.25)

# PLAY ------------------------------------------------------------------------------------
pl = [h for h in holes if kind(h) == "play"][0]
circ(gold, pl[0], pl[1], 7.0, 0.3)
n = 36
for i in range(n):
    a = 360 * i / n
    t = math.radians(a)
    line(silk, pl[0] + 8.2 * math.sin(t), pl[1] - 8.2 * math.cos(t), pl[0] + 9.2 * math.sin(t), pl[1] - 9.2 * math.cos(t), 0.2)
text(silk, "PLAY", 227 * PX, pl[1] + 1.0, 2.9, "start", 0.28)

# model buttons + LEDs -----------------------------------------------------------------
btns = sorted([h for h in holes if kind(h) == "btn"])
leds = sorted([h for h in holes if kind(h) == "led"])
for (x, y, r) in leds:
    circ(gold, x, y, r + 1.0, 0.3)
    circ(silk, x, y, r + 1.9, 0.15)
for i, (x, y, r) in enumerate(btns):
    circ(silk, x, y, r + 1.1, 0.2)
    text(silk, "MODEL", x + 0.12, y + r + 1.1 + 2.7, 2.0, "middle", 0.3)
    if i == 0:
        poly(gold, [(x - 4.9, y - 1.0), (x - 6.0, y), (x - 4.9, y + 1.0)], 0.28, closed=False)
    else:
        poly(gold, [(x + 4.9, y - 1.0), (x + 6.0, y), (x + 4.9, y + 1.0)], 0.28, closed=False)

# ---------------------------------------------------------------- output
cutline = [(x, y, r) for (x, y, r) in holes]


def edge_elems():
    out = ['<rect x="0" y="0" width="%s" height="%s" fill="none" stroke-width="0.254"/>' % (W, H)]
    for (x, y, r) in cutline:
        out.append('<circle cx="%s" cy="%s" r="%s" fill="none" stroke-width="0.254"/>' % (f(x), f(y), f(r)))
    return out


def doc(body, color, bg=None, extra=""):
    head = ('<svg xmlns="http://www.w3.org/2000/svg" width="%smm" height="%smm" viewBox="0 0 %s %s">'
            '<style>.fill{fill:%s}</style>' % (W, H, W, H, color))
    return head + (bg or "") + '<g stroke="%s" fill="none">' % color + "".join(body) + "</g>" + extra + "</svg>"


def w(name, s):
    open(os.path.join(HERE, name), "w", encoding="utf8").write(s)


w("F_SilkS.svg", doc(silk, "#000000").replace('class="fill"', 'fill="#000000"'))
w("F_Silver_Cu_Mask.svg", doc(gold, "#000000").replace('class="fill"', 'fill="#000000"'))
w("Edge_Cuts.svg", doc(edge_elems(), "#000000"))

SILK, GOLD, MASK = "#f4f4f0", "#b9bec7", "#0c0c0e"   # GOLD var = silver HASL colour
holes_svg = "".join('<circle cx="%s" cy="%s" r="%s" fill="#d8d8d8" stroke="none"/>' % (f(x), f(y), f(r)) for x, y, r in holes)
prev = ('<svg xmlns="http://www.w3.org/2000/svg" width="%smm" height="%smm" viewBox="0 0 %s %s">' % (W, H, W, H)
        + '<rect width="%s" height="%s" fill="%s"/>' % (W, H, MASK)
        + '<style>.fill{fill:%s}</style>' % GOLD
        + '<g stroke="%s" fill="none">%s</g>' % (GOLD, "".join(gold))
        + '<style>.s .fill{fill:%s}</style>' % SILK
        + '<g class="s" stroke="%s" fill="none"><style>.s .fill{fill:%s}</style>%s</g>' % (SILK, SILK, "".join(silk))
        + holes_svg + "</svg>")
w("preview.svg", prev)
print("holes:", len(holes), "silk:", len(silk), "gold:", len(gold))


