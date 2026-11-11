"""Vector placeholders for the moe-office scene -> <mod>/scene/<theme>/*.svg.

Usage: scene_art.py <mod>/scene            (every theme)
       scene_art.py <mod>/scene <theme>    (one theme)
Themes (THEMES below): "pastel", the pastel office, and "jirai", pink and black with lace
and ribbons. Every theme draws the same pieces at the same sizes, so the room's layout
doesn't change; only the colours and the trimmings do.

Every asset is drawn in scene units (1 unit = U px at runtime) with the floor (or the
thing it stands on) at the bottom edge of its viewBox. scene.js lists them with the same
w x h; to replace one with a drawn image later, export a PNG of the same aspect ratio and
point its `src` in scene.js at it.
"""
import os, sys, subprocess

# Each theme's colours, by the role they play in the pastel office: LAV is the desks, couch
# and clock; MINT the door, counter, lamp and leaves; SKY the water and glass; BUTTER the
# stars and bells; PEACH the flower pot; WOOD the floor and boxes. The Moe Office scene.js
# has the matching wall and floor colours (THEMES there).
THEMES = {
    "pastel": dict(
        INK="#7a6178", CREAM=("#fffaf3", "#f3e6da"), PINK=("#ffd6e2", "#ffb3c9", "#f28daa"),
        LAV=("#e6dcfa", "#cbb8f0", "#a993dc"), MINT=("#d4f3e8", "#a8e3cf", "#79c9ad"),
        SKY=("#d6ecff", "#a9d3f5"), BUTTER=("#fff0b8", "#ffd977"), PEACH=("#ffe0cc", "#ffc2a1"),
        WOOD=("#f2d2ad", "#dfb185"), WALL="#fdf0f3", SCREEN="#5a4a63", SCREEN2="#6e5c78", CURTAIN="#ffd6e2"),
    "jirai": dict(
        INK="#3b2433", CREAM=("#fff7fa", "#f6d9e3"), PINK=("#ffc9da", "#ff9dbb", "#f06b97"),
        LAV=("#3a2d38", "#2a1f29", "#f06b97"), MINT=("#3a2d38", "#ff9dbb", "#2a1f29"),
        SKY=("#ffe3ec", "#ffb3c9"), BUTTER=("#f7f1f5", "#d9c7d3"), PEACH=("#3a2d38", "#2a1f29"),
        WOOD=("#f6d9e3", "#3a2d38"), WALL="#fff0f5", SCREEN="#2a1f29", SCREEN2="#3a2d38", CURTAIN="#ffffff",
        LACE=("#ffffff", "#f6c4d5"), RAIL_LACE="#2a1f29"),
    # Gothic lolita, for dark mode: a dark room, the furniture in mid-tone plum and wine so it
    # shows against it, silver-white lace, crosses and roses.
    "gothic": dict(
        INK="#160e1a", CREAM=("#ddd3e4", "#a99bb6"), PINK=("#8c3d5e", "#6e2b48", "#c4506f"),
        LAV=("#56406a", "#45325a", "#b9a3d6"), MINT=("#56406a", "#7a2e4c", "#2c2036"),
        SKY=("#6a5a8c", "#9a8ac0"), BUTTER=("#e4dfeb", "#b8afc6"), PEACH=("#3a2b48", "#2c2036"),
        WOOD=("#6a5478", "#2c2036"), WALL="#241b2d", SCREEN="#140d18", SCREEN2="#2c2036", CURTAIN="#6e2340",
        LACE=("#ece4f2", "#56406a"), RAIL_LACE="#ece4f2"),
}

if len(sys.argv) < 3:  # every theme, each in its own run
    for name in THEMES:
        subprocess.run([sys.executable, "-I", __file__, sys.argv[1], name], check=True)
    sys.exit()

THEME = sys.argv[2]
OUT = f"{sys.argv[1]}/{THEME}"
os.makedirs(OUT, exist_ok=True)
T = THEMES[THEME]
J = THEME in ("jirai", "gothic")  # the lace and ribbons
G = THEME == "gothic"  # and crosses and roses

INK = T["INK"]       # outline
SW = 0.45            # stroke width in units
CREAM, CREAM2 = T["CREAM"]
PINK, PINK2, PINK3 = T["PINK"]
LAV, LAV2, LAV3 = T["LAV"]
MINT, MINT2, MINT3 = T["MINT"]
SKY, SKY2 = T["SKY"]
BUTTER, BUTTER2 = T["BUTTER"]
PEACH, PEACH2 = T["PEACH"]
WOOD, WOOD2 = T["WOOD"]
WALL = T["WALL"]
SCREEN_C, SCREEN_C2 = T["SCREEN"], T["SCREEN2"]
LACE, LACE_HOLE = T.get("LACE", ("#ffffff", "#f6c4d5"))

def s(fill, extra=""):
    return f'fill="{fill}" stroke="{INK}" stroke-width="{SW}" stroke-linejoin="round" stroke-linecap="round" {extra}'

def write(name, w, h, body, turns=False):
    """<name>.svg faces right. Things that turn around (turns=True, only the cat so far) also
    get <name>_l.svg, their mirror image: Herdr can't flip an element when drawing it."""
    head = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w * 8}" height="{h * 8}">'
    open(f"{OUT}/{name}.svg", "w").write(f"{head}{body}</svg>")
    if turns:
        open(f"{OUT}/{name}_l.svg", "w").write(f'{head}<g transform="translate({w} 0) scale(-1 1)">{body}</g></svg>')

def heart(cx, cy, r, fill, stroke=True):
    d = (f"M{cx} {cy + r * 0.9} C{cx - r * 1.6} {cy - r * 0.1} {cx - r * 0.9} {cy - r * 1.3} {cx} {cy - r * 0.45} "
         f"C{cx + r * 0.9} {cy - r * 1.3} {cx + r * 1.6} {cy - r * 0.1} {cx} {cy + r * 0.9}Z")
    return f'<path d="{d}" {s(fill) if stroke else f"fill={chr(34)}{fill}{chr(34)}"}/>'

def star(cx, cy, r, fill, stroke=True):
    import math
    pts = []
    for k in range(10):
        a = -math.pi / 2 + k * math.pi / 5
        rr = r if k % 2 == 0 else r * 0.45
        pts.append(f"{cx + rr * math.cos(a):.2f},{cy + rr * math.sin(a):.2f}")
    return f'<polygon points="{" ".join(pts)}" {s(fill) if stroke else f"fill={chr(34)}{fill}{chr(34)}"}/>'

def lace(x, y, w, r=0.55, fill=None, holes=True):
    """A lace trim hanging down from the line y, x to x + w: scallops with a hole in each."""
    fill = fill or LACE
    n = max(1, round(w / (2 * r)))
    r = w / n / 2
    d = f"M{x} {y} " + " ".join(f"a{r:.3f} {r:.3f} 0 0 0 {2 * r:.3f} 0" for _ in range(n)) + f" Z"
    out = f'<path d="{d}" fill="{fill}" stroke="{INK}" stroke-width="{SW * 0.5}" stroke-linejoin="round"/>'
    if holes:
        out += "".join(f'<circle cx="{x + r * (2 * k + 1):.3f}" cy="{y + r * 0.45:.3f}" r="{r * 0.28:.3f}" fill="{LACE_HOLE if fill == LACE else INK}"/>' for k in range(n))
    return out

def cross(cx, cy, h, fill):
    """A cross, h tall, centred on (cx, cy)."""
    w = h * 0.22
    return (f'<path d="M{cx - w / 2} {cy - h / 2} h{w} v{h * 0.25} h{h * 0.22} v{w} h{-h * 0.22} v{h * 0.75 - w} h{-w} '
            f'v{-(h * 0.75 - w)} h{-h * 0.22} v{-w} h{h * 0.22} Z" {s(fill)}/>')

def rose(cx, cy, r, fill):
    """A rose seen from above: a round bloom with a swirl."""
    return (circ(cx, cy, r, fill) +
            f'<path d="M{cx - r * 0.5} {cy} a{r * 0.5} {r * 0.5} 0 1 1 {r * 0.5} {r * 0.5} a{r * 0.3} {r * 0.3} 0 1 1 {-r * 0.1} {-r * 0.6}" '
            f'fill="none" stroke="{INK}" stroke-width="{SW * 0.6}" stroke-linecap="round"/>')

def bow(cx, cy, size, fill, tails=True):
    """A ribbon bow centred on (cx, cy), size wide."""
    h = size / 2
    parts = [
        f'<path d="M{cx} {cy} C{cx - h * 0.4} {cy - h * 0.9} {cx - h} {cy - h * 0.7} {cx - h} {cy - h * 0.1} '
        f'C{cx - h} {cy + h * 0.5} {cx - h * 0.4} {cy + h * 0.5} {cx} {cy} Z" {s(fill)}/>',
        f'<path d="M{cx} {cy} C{cx + h * 0.4} {cy - h * 0.9} {cx + h} {cy - h * 0.7} {cx + h} {cy - h * 0.1} '
        f'C{cx + h} {cy + h * 0.5} {cx + h * 0.4} {cy + h * 0.5} {cx} {cy} Z" {s(fill)}/>',
    ]
    if tails:
        parts.insert(0, f'<path d="M{cx - h * 0.1} {cy} L{cx - h * 0.55} {cy + h * 0.9} L{cx - h * 0.2} {cy + h * 0.75} Z '
                        f'M{cx + h * 0.1} {cy} L{cx + h * 0.55} {cy + h * 0.9} L{cx + h * 0.2} {cy + h * 0.75} Z" {s(fill)}/>')
    parts.append(f'<ellipse cx="{cx}" cy="{cy}" rx="{h * 0.22:.3f}" ry="{h * 0.26:.3f}" {s(fill)}/>')
    return "".join(parts)

def rect(x, y, w, h, fill, rx=0.6, extra=""):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" {s(fill, extra)}/>'

def circ(cx, cy, r, fill, stroke=True):
    return f'<circle cx="{cx}" cy="{cy}" r="{r}" ' + (s(fill) if stroke else f'fill="{fill}"') + '/>'

# --- desk: front of the desk, drawn over a seated doll. Top surface at height 12. --------
# 29 x 14, placed at desk x + 10 units.
write("desk", 29, 14, "".join([
    rect(0.9, 3, 1.6, 10.6, LAV2, 0.6),                        # left leg; the doll's legs show beside it
    rect(17.6, 3, 10.4, 10.6, LAV, 1),                         # drawer unit
    rect(18.8, 4.4, 8, 3.6, LAV2, 0.8), rect(18.8, 8.6, 8, 3.6, LAV2, 0.8),
    *([heart(22.8, 6.2, 0.7, PINK2), heart(22.8, 10.4, 0.7, PINK2)] if J else [circ(22.8, 6.2, 0.55, PINK3), circ(22.8, 10.4, 0.55, PINK3)]),
    lace(17.6, 3.4, 10.4, 0.45) if J else "",                   # lace under the top, over the drawers
    rect(0.3, 1.4, 28.4, 2.2, CREAM, 1.1),                     # table top
    heart(11, 2.5, 0.6, PINK2),
    bow(28, 2.6, 2.2, PINK3) if J else "",
    rect(1.2, 0.4, 7, 1.2, PINK, 0.5),                         # keyboard under her hands (slot x 11-18)
    *[f'<rect x="{2.0 + k * 1.2}" y="0.75" width="0.7" height="0.4" rx="0.15" fill="{PINK3}"/>' for k in range(5)],
]))
DESK_X = 10  # units from the desk slot's left edge

# cat shelf: 14 x 5, a plank on the wall for the cat, top at y 0.6, two brackets under it and
# a paw print on its front. Put up in the gaps between the things on the wall.
def paw(cx, cy, r, fill):
    return (f'<ellipse cx="{cx}" cy="{cy + r * 0.35}" rx="{r * 0.7}" ry="{r * 0.55}" fill="{fill}"/>'
            + "".join(circ(cx + dx * r, cy - 0.55 * r, r * 0.26, fill, False) for dx in (-0.7, -0.24, 0.24, 0.7)))
write("catshelf", 14, 5, "".join([
    f'<path d="M3 2.2 v2.4 l1.8 -2.4 Z" {s(WOOD2 if not J else LAV2)}/>',
    f'<path d="M11 2.2 v2.4 l-1.8 -2.4 Z" {s(WOOD2 if not J else LAV2)}/>',
    lace(0.6, 2.2, 12.8, 0.5) if J else "",
    rect(0.4, 0.6, 13.2, 1.6, PINK if not J else LAV, 0.5),
    paw(7, 1.45, 0.62, PINK3 if not J else PINK2),
]))

# lamp: stands on the desk top, 5 x 9, at slot x 34
write("lamp", 5, 9, "".join([
    f'<path d="M2.5 8.5 L2.5 3.5" stroke="{INK}" stroke-width="{SW * 1.6}" stroke-linecap="round"/>',
    rect(1, 8, 3, 1, MINT2, 0.4),
    f'<path d="M0.4 4 Q2.5 -0.6 4.6 4 Z" {s(MINT)}/>',
    lace(0.4, 4, 4.2, 0.35, PINK2, False) if J else "",
    circ(2.5, 1.3, 0.35, PINK2, False),
]))

# monitor: 14 x 13, bottom on the desk top, at slot x 21. Screen hole at (1.6,1.6) 10.8 x 7.4.
SCREEN = (1.6, 1.6, 10.8, 7.4)
write("monitor", 14, 13, "".join([
    # cat ears
    f'<path d="M2 2 L3.2 -0.2 L5 1.6 Z" {s(SCREEN_C)}/>', f'<path d="M12 2 L10.8 -0.2 L9 1.6 Z" {s(SCREEN_C)}/>',
    f'<path d="M2.9 1.4 L3.3 0.6 L4 1.3 Z" fill="{PINK2}"/>', f'<path d="M11.1 1.4 L10.7 0.6 L10 1.3 Z" fill="{PINK2}"/>',
    f'<path d="M0.6 1.2 h12.8 a0.9 0.9 0 0 1 0.9 0.9 v8 a0.9 0.9 0 0 1 -0.9 0.9 h-12.8 a0.9 0.9 0 0 1 -0.9 -0.9 v-8 a0.9 0.9 0 0 1 0.9 -0.9 Z '
    f'M1.6 1.6 v7.4 h10.8 v-7.4 Z" fill-rule="evenodd" {s(SCREEN_C)}/>',
    rect(6, 10.9, 2, 1.2, SCREEN_C, 0.2), rect(4, 12, 6, 0.9, SCREEN_C2, 0.45),
    circ(7, 10.1, 0.35, PINK2, False),
    bow(12.6, 1.6, 2.4, PINK2) if J else "",
]))

# chair: 12 x 20, behind the seated doll, at slot x 2. Seat top at height 7.
write("chair", 12, 20, "".join([
    f'<path d="M1.4 3.2 L1.6 1 L3 2.4 Z" {s(PINK2)}/>', f'<path d="M4.6 2.4 L5.8 1 L5.9 3.2 Z" {s(PINK2)}/>',
    rect(0.8, 2.2, 5.6, 11, PINK, 2.4),                        # back
    heart(3.6, 6.6, 1.1, CREAM),
    bow(3.6, 2.6, 3.4, INK if J else PINK2) if J else "",
    rect(1, 12, 10.4, 2.2, PINK2, 1.1),                        # seat
    lace(1.4, 14.2, 9.6, 0.4) if J else "",
    rect(5.2, 14.2, 1.6, 3.6, CREAM2, 0.3),
    f'<path d="M1.6 18.6 Q6 16.8 10.4 18.6" fill="none" stroke="{INK}" stroke-width="{SW * 1.6}" stroke-linecap="round"/>',
    circ(1.8, 19.2, 0.6, LAV2), circ(10.2, 19.2, 0.6, LAV2), circ(6, 19.2, 0.6, LAV2),
]))

# couch: 36 x 17, seat top at height 7.
write("couch", 36, 17, "".join([
    rect(2.5, 1, 31, 10, LAV, 3),                              # back
    *[f'<path d="M{x} 2.6 v7" stroke="{LAV2}" stroke-width="0.5" stroke-linecap="round"/>' for x in (12.8, 23.2)],
    rect(2.2, 9.4, 31.6, 4.4, LAV2, 1.6),                      # seat
    rect(0.2, 6.2, 4.2, 8.6, LAV, 2),  rect(31.6, 6.2, 4.2, 8.6, LAV, 2),  # arms
    rect(3.6, 14.6, 1.4, 2, WOOD2, 0.4), rect(31, 14.6, 1.4, 2, WOOD2, 0.4),
    heart(7.4, 6.4, 2.2, PINK2), heart(28.4, 6.6, 2, MINT2),
    *([lace(2.6, 13.8, 30.8, 0.55), cross(18, 5.4, 4, BUTTER) if G else bow(18, 5.4, 4, PINK2)] if J else [star(18, 5.6, 1.4, BUTTER2)]),
]))

# water cooler: 11 x 25
write("cooler", 11, 25, "".join([
    rect(2.6, 0.6, 5.8, 8.6, SKY, 2.4),                        # bottle
    f'<path d="M3.6 2.4 v4.6" stroke="#ffffff" stroke-width="0.6" stroke-linecap="round"/>',
    heart(5.5, 4.6, 1.1, "#ffffff"),
    rect(1, 9, 9, 15.4, CREAM, 1.6),
    rect(2.6, 11.4, 5.8, 3.4, MINT, 0.8),
    circ(4, 13.1, 0.55, PINK3), circ(7, 13.1, 0.55, SKY2),
    rect(2.6, 19, 5.8, 3.6, CREAM2, 0.8),
    rect(9.6, 13, 1.2, 5, "#ffffff", 0.3),
    bow(5.5, 9.2, 3.6, PINK3) if J else "",
]))

# counter: 36 x 21, top at height 11. On it, left to right: a coffee machine, a plate of
# cookies (the tea-time cake goes here, x 10.5 to 20.5), a tea set, and a dessert case.
COUNTER_TOP = 11
write("counter", 36, 21, "".join([
    rect(0.6, 10.6, 34.8, 10, MINT, 1),
    rect(2, 12.6, 10, 6.8, MINT2, 0.8), rect(13, 12.6, 10, 6.8, MINT2, 0.8), rect(24, 12.6, 10, 6.8, MINT2, 0.8),
    *[heart(x, 16, 0.6, CREAM) for x in (11, 14, 22, 25)],
    rect(0, 9.6, 36, 1.6, CREAM, 0.8),
    lace(0.6, 11.2, 34.8, 0.5) if J else "",
    # coffee machine (cat ears), a cup under the spout
    f'<path d="M2.4 2.4 L3.2 0.6 L4.4 2 Z" {s(PINK2)}/>', f'<path d="M8.6 2.4 L7.8 0.6 L6.6 2 Z" {s(PINK2)}/>',
    rect(1.8, 1.6, 7.4, 8, PINK, 1.4),
    rect(3, 3, 5, 2, CREAM, 0.6), circ(4, 4, 0.35, MINT3, False), circ(5.5, 4, 0.35, PINK3, False),
    rect(3.4, 6.2, 4.2, 0.8, CREAM2, 0.3), rect(4.4, 7.6, 2.2, 2, CREAM, 0.4),
    # cookies on a plate
    f'<ellipse cx="15.5" cy="9.4" rx="3.4" ry="0.5" {s(CREAM)}/>',
    circ(14.2, 8.6, 0.8, WOOD2), circ(16, 8.4, 0.8, WOOD), circ(15.1, 7.6, 0.75, WOOD2),
    # tea set: a teapot and a cup on a saucer
    f'<path d="M20.6 6.6 q-1.2 -0.4 -1.5 1.4" fill="none" stroke="{INK}" stroke-width="0.5" stroke-linecap="round"/>',
    f'<path d="M25.6 6.4 q1.4 0.4 0.9 2" fill="none" stroke="{INK}" stroke-width="0.5" stroke-linecap="round"/>',
    f'<ellipse cx="23" cy="7.6" rx="2.6" ry="2" {s(CREAM)}/>',
    f'<path d="M21.2 5.8 q1.8 -1.2 3.6 0 Z" {s(PINK2)}/>', circ(23, 4.8, 0.45, PINK3),
    heart(23, 7.7, 0.6, PINK2),
    f'<ellipse cx="23" cy="9.5" rx="2.2" ry="0.35" fill="{CREAM2}"/>',
    # dessert case: two glass shelves of cake slices
    rect(27.2, 2.6, 8, 7, SKY, 0.6, 'fill-opacity="0.55"'),
    f'<path d="M27.4 6.2 h7.6" stroke="{INK}" stroke-width="0.3"/>',
    *[f'<path d="M{x} {y} l1.5 -1.4 l0.2 1.4 Z" {s(c)}/>' for x, y, c in
      [(28, 5.8, PINK2), (30.4, 5.8, BUTTER2), (32.8, 5.8, CREAM), (28.4, 9.2, CREAM), (30.8, 9.2, PINK2), (33.2, 9.2, WOOD2)]],
    rect(26.9, 2.2, 8.6, 0.8, LAV2 if J else PINK2, 0.4),
]))
# tea time: a cake on the counter, 10 x 5 (bottom on the counter top), and its box, carried, 9 x 3
write("cake", 10, 5, "".join([
    f'<ellipse cx="5" cy="4.6" rx="4.8" ry="0.4" {s(CREAM2)}/>',
    rect(1, 2.4, 8, 2.2, CREAM, 0.6),
    f'<path d="M1 3 q1 0.8 2 0 q1 0.8 2 0 q1 0.8 2 0 q1 0.8 2 0" fill="none" stroke="{PINK2}" stroke-width="0.6" stroke-linecap="round"/>',
    rect(2.6, 0.8, 4.8, 1.7, PINK, 0.6),
    circ(3.6, 0.6, 0.5, "#ef5b6f"), circ(5, 0.5, 0.5, "#ef5b6f"), circ(6.4, 0.6, 0.5, "#ef5b6f"),
]))
write("cake_carry", 9, 3, rect(0.3, 0.3, 8.4, 2.4, CREAM, 0.5) + f'<path d="M4.5 0.3 v2.4" stroke="{PINK3}" stroke-width="0.6"/>' + bow(4.5, 0.4, 2.6, PINK3, tails=False))

# bookshelf: 14 x 26, at the right end of the room. Books, and plushies on the shelves.
BOOKS = [PINK2, SKY2, MINT2, BUTTER2, LAV2, PEACH2, PINK3, CREAM2]
def books(x0, y, n, seed):
    out, x = [], x0
    for k in range(n):
        w, h = 0.9 + ((seed + k * 7) % 3) * 0.25, 3.6 + ((seed + k * 5) % 4) * 0.4
        out.append(rect(x, y - h, w, h, BOOKS[(seed + k) % len(BOOKS)], 0.2))
        x += w + 0.1
    return "".join(out)
def bear(cx, by, r, fill):
    """A small plush bear sitting with its bottom at by."""
    return "".join([circ(cx - r * 0.8, by - r * 2.6, r * 0.38, fill), circ(cx + r * 0.8, by - r * 2.6, r * 0.38, fill),
                    f'<ellipse cx="{cx}" cy="{by - r * 0.75}" rx="{r * 0.95}" ry="{r * 0.8}" {s(fill)}/>',
                    circ(cx, by - r * 2.05, r * 0.85, fill),
                    circ(cx - r * 0.3, by - r * 2.1, r * 0.1, INK, False), circ(cx + r * 0.3, by - r * 2.1, r * 0.1, INK, False),
                    f'<ellipse cx="{cx}" cy="{by - r * 1.75}" rx="{r * 0.3}" ry="{r * 0.2}" fill="{CREAM}"/>'])
write("bookshelf", 14, 26, "".join([
    rect(0.4, 0.6, 13.2, 25, LAV, 0.8), rect(1.4, 1.6, 11.2, 23, LAV2, 0.4),
    *[rect(1.2, y, 11.6, 0.8, LAV, 0.3) for y in (7.6, 13.8, 20)],
    books(1.8, 7.6, 6, 1), bear(10.4, 7.6, 1.2, PEACH2 if not G else CREAM2),
    bear(3.2, 13.8, 1.1, PINK2), books(5.2, 13.8, 5, 4),  # 5 books fit inside the frame (ends at x 11.7)
    books(1.8, 20, 4, 2), f'<ellipse cx="9.4" cy="18.6" rx="2.2" ry="1.4" {s(CREAM)}/>', circ(10.8, 17.2, 0.9, CREAM),
    circ(11.1, 17, 0.12, INK, False), heart(9.2, 18.4, 0.5, PINK2),  # a sleeping plush cat
    rect(0.6, 25, 12.8, 0.8, LAV2, 0.3),
    bow(7, 0.9, 3.4, PINK3) if J else "",
]))

# Desk things, two per character, standing on the desk top (y 10) from slot x 31 to 39: a
# small one in front of the monitor's right corner (x 0 to 3, up to 2.6 tall), a taller one
# beside the monitor (x 4 to 8).
def carton(x, fill, cap):
    return rect(x, 7.4, 2, 2.6, fill, 0.3) + f'<path d="M{x} 7.4 l1 -0.8 l1 0.8" {s(cap)}/>' + heart(x + 1, 8.8, 0.45, CREAM)
def can(x, fill):
    return rect(x, 7.3, 1.6, 2.7, fill, 0.4) + f'<path d="M{x + 0.9} 7.9 l-0.4 0.8 h0.5 l-0.4 0.8" fill="none" stroke="{BUTTER2}" stroke-width="0.3"/>'
def cat_plush(cx, fill):
    return "".join([f'<path d="M{cx - 1.3} 6.2 l0.2 -1.3 l0.9 0.8 Z" {s(fill)}/>', f'<path d="M{cx + 1.3} 6.2 l-0.2 -1.3 l-0.9 0.8 Z" {s(fill)}/>',
                    f'<ellipse cx="{cx}" cy="8.8" rx="1.5" ry="1.2" {s(fill)}/>', circ(cx, 6.6, 1.4, fill),
                    circ(cx - 0.5, 6.6, 0.14, INK, False), circ(cx + 0.5, 6.6, 0.14, INK, False),
                    f'<path d="M{cx - 0.25} 7.1 q0.25 0.25 0.5 0" fill="none" stroke="{INK}" stroke-width="0.15"/>'])
SETS = {
    "jirai": [  # strawberry milk, a pink bear with a bow
        carton(0.4, PINK, PINK2),
        bear(6, 10, 1.15, PINK2), bow(6, 7.4, 1.4, INK if not G else PINK3, tails=False),
    ],
    "intern": [  # a juice box, a pencil cup
        carton(0.4, BUTTER2, BUTTER) + f'<path d="M1.8 6.8 v-1.2 l0.6 -0.4" fill="none" stroke="{INK}" stroke-width="0.3"/>',
        *[f'<path d="M{x} 7.4 l{d} -2.6" stroke="{c}" stroke-width="0.45" stroke-linecap="round"/>' for x, d, c in [(5.3, -0.3, PINK3), (5.8, 0, BUTTER2), (6.3, 0.4, SKY2)]],
        rect(4.8, 7.4, 2.2, 2.6, CREAM, 0.3),
    ],
    "designer-cute": [  # a cup of tea, a tulip in a vase
        f'<ellipse cx="1.6" cy="9.8" rx="1.5" ry="0.3" {s(CREAM2)}/>', f'<path d="M0.6 8 h2 l-0.3 1.6 h-1.4 Z" {s(CREAM)}/>',
        f'<path d="M2.6 8.3 q0.7 0.2 0.1 0.9" fill="none" stroke="{INK}" stroke-width="0.3"/>',
        f'<path d="M6 8 Q5.8 5.6 6 4.2" fill="none" stroke="{MINT3}" stroke-width="0.4"/>',
        f'<path d="M5.1 4.6 q0.9 -2 1.8 0 q-0.9 0.8 -1.8 0 Z" {s(PINK2)}/>',
        f'<path d="M5.2 10 q-0.6 -1.6 0.3 -2.4 h1 q0.9 0.8 0.3 2.4 Z" {s(SKY)}/>',
    ],
    "engineer-hoodie": [  # an energy drink, a grey cat plush
        can(0.6, SKY2), cat_plush(6, "#c8c5d6"),
    ],
    "wavy-blouse": [  # a pudding, a hand mirror
        f'<path d="M0.4 8 h2.6 l-0.35 2 h-1.9 Z" {s(BUTTER)}/>', f'<path d="M0.4 8 q1.3 -0.9 2.6 0 Z" {s("#c98a5a")}/>',
        circ(1.7, 7.3, 0.4, PINK3),
        rect(5.6, 7.4, 0.8, 2.6, PINK2, 0.3), circ(6, 5.8, 1.7, PINK2), circ(6, 5.8, 1.15, SKY, False),
        f'<path d="M5.5 5.3 l0.5 -0.4" stroke="#ffffff" stroke-width="0.3" stroke-linecap="round"/>', heart(6, 3.7, 0.5, PINK3),
    ],
    "twintail-blazer": [  # a cat mug, a photo frame
        f'<path d="M2.6 8.3 q0.9 0.2 0.2 1.1" fill="none" stroke="{INK}" stroke-width="0.3"/>',
        f'<path d="M0.5 7.6 l0.3 -0.8 l0.5 0.8 Z M2.6 7.6 l-0.3 -0.8 l-0.5 0.8 Z" {s(CREAM)}/>',
        rect(0.4, 7.5, 2.3, 2.5, CREAM, 0.3),
        circ(1.15, 8.5, 0.13, INK, False), circ(1.95, 8.5, 0.13, INK, False),
        rect(4.6, 4.8, 3.2, 4.4, PINK2, 0.3), rect(5.1, 5.3, 2.2, 3.4, SKY, 0.2), heart(6.2, 7, 0.55, PINK3),
        f'<path d="M5.4 9.2 l-0.4 0.8 M7 9.2 l0.4 0.8" stroke="{INK}" stroke-width="0.3" stroke-linecap="round"/>',
    ],
    "bob-jacket": [  # a handheld game, a bunny plush
        rect(0.2, 7.8, 3.2, 2.2, LAV2, 0.5), rect(1.1, 8.15, 1.4, 1.1, MINT, 0.15),
        circ(0.65, 8.9, 0.22, PINK3, False), circ(2.95, 8.7, 0.18, BUTTER2, False), circ(2.95, 9.25, 0.18, SKY2, False),
        f'<path d="M5.3 6.4 q-0.5 -2.6 0.4 -2.8 q0.6 0.4 0.3 2.8 Z" {s(CREAM)}/>',
        f'<path d="M6.7 6.4 q-0.1 -2.6 0.6 -2.8 q0.8 0.3 0 2.8 Z" {s(CREAM)}/>',
        f'<ellipse cx="6.2" cy="8.9" rx="1.6" ry="1.2" {s(CREAM)}/>', circ(6.2, 7, 1.35, CREAM),
        circ(5.7, 7, 0.14, INK, False), circ(6.7, 7, 0.14, INK, False), circ(5.4, 7.4, 0.25, PINK2, False), circ(7, 7.4, 0.25, PINK2, False),
    ],
}
for who, parts in SETS.items():
    write(f"set_{who}", 8, 10, "".join(parts))

# moving box: 7 x 6
write("box", 7, 6, "".join([
    f'<path d="M2.4 1.6 q-0.4 -1.6 0.6 -1.4 q0.8 0.4 0.2 1.4 Z" {s(MINT2)}/>',
    rect(0.3, 1.6, 6.4, 4.1, WOOD, 0.4), f'<path d="M0.3 2.6 h6.4" stroke="{INK}" stroke-width="{SW}"/>',
    heart(3.5, 4.1, 0.6, PINK2),
]))

# plant: 10 x 20
write("plant", 10, 20, "".join([
    f'<path d="M5 13 Q4.6 7 5 3" fill="none" stroke="{MINT3}" stroke-width="0.6"/>',
    *[f'<ellipse cx="{x}" cy="{y}" rx="2.1" ry="1.3" transform="rotate({r} {x} {y})" {s(c)}/>'
      for x, y, r, c in ([(3, 9.6, -30, "#2f4a3c"), (7, 8.4, 30, "#2f4a3c"), (3.4, 6, -40, "#3d5c4b"), (6.6, 4.8, 40, "#3d5c4b"), (5, 2.4, 0, "#2f4a3c")] if G else
                         [(3, 9.6, -30, MINT2), (7, 8.4, 30, MINT2), (3.4, 6, -40, PINK if J else MINT), (6.6, 4.8, 40, PINK if J else MINT), (5, 2.4, 0, MINT2)])],
    *([rose(3.6, 4.4, 1.3, PINK3), rose(6.8, 6.6, 1.1, PINK3), rose(5, 1.6, 1, PINK3)] if G else []),
    bow(5, 12.4, 3, PINK3) if J else "",
    f'<path d="M1.6 12.6 h6.8 l-0.8 6.8 a0.6 0.6 0 0 1 -0.6 0.5 h-4 a0.6 0.6 0 0 1 -0.6 -0.5 Z" {s(PEACH)}/>',
    rect(1, 12, 8, 1.6, PEACH2, 0.6),
    circ(3.9, 16, 0.3, CREAM if J else INK, False), circ(6.1, 16, 0.3, CREAM if J else INK, False),
    f'<path d="M4.4 17 q0.6 0.6 1.2 0" fill="none" stroke="{CREAM if J else INK}" stroke-width="0.3" stroke-linecap="round"/>',
    circ(3.2, 16.8, 0.4, PINK2, False), circ(6.8, 16.8, 0.4, PINK2, False),
]))

# door: 17 x 29 (bottom at the wall's foot)
def arch(x, y, w, h, fill):
    r = w / 2
    return f'<path d="M{x} {y + h} V{y + r} A{r} {r} 0 0 1 {x + w} {y + r} V{y + h} Z" {s(fill)}/>'
def door(open_):
    inner = (arch(2.2, 2.6, 12.6, 26, SCREEN_C) + rect(2.2, 23.6, 12.6, 5, "#7d6a88", 0.2)) if open_ else "".join([
        arch(2.2, 2.6, 12.6, 26, MINT),
        circ(8.5, 9.4, 3, SKY), heart(8.5, 9.6, 1.1, PINK2),
        rect(4.4, 15.4, 8.2, 9.6, MINT2, 1),
        circ(12.6, 17.6, 0.7, BUTTER2),
    ])
    return "".join([arch(0.6, 0.6, 15.8, 28.4, CREAM), inner,
                    f'<path d="M2.2 28.6 h12.6" stroke="{INK}" stroke-width="{SW}"/>',
                    bow(8.5, 2.2, 4.4, PINK3) if J else ""])
write("door", 17, 29, door(False))
write("door_open", 17, 29, door(True))
# a little sign above the door: 12 x 4
write("door_sign", 12, 4, rect(0.3, 0.3, 11.4, 3.4, PINK, 1.6) + (
    cross(2, 2, 2.4, BUTTER) + cross(10, 2, 2.4, BUTTER) if G else
    heart(2, 2, 0.9, INK) + heart(10, 2, 0.9, INK) if J else star(2, 2, 0.9, BUTTER2) + star(10, 2, 0.9, BUTTER2)))

# window frame: 30 x 26, a square hole (glass) over the sky divs; the rest is wall colour.
# Glass: x 3..27, y 3..23.
GLASS = (3, 3, 24, 20)
hole = "M3 3 H27 V23 H3 Z"
write("window", 30, 26, "".join([
    f'<path d="M0 0 H30 V26 H0 Z {hole}" fill="{WALL}" fill-rule="evenodd"/>',
    f'<path d="M2.4 1.6 H27.6 Q28.4 1.6 28.4 2.4 V24.4 H1.6 V2.4 Q1.6 1.6 2.4 1.6 Z {hole}" fill-rule="evenodd" {s(LAV if J else CREAM)}/>',
    f'<path d="M15 3.2 V23 M3 15 H27" stroke="{LAV if J else CREAM}" stroke-width="1"/>',
    f'<path d="M15 3.2 V23 M3 15 H27" stroke="{INK}" stroke-width="0.25" stroke-dasharray="0"/>',
    rect(0.6, 23.2, 28.8, 2.2, CREAM2, 1),                     # sill
    # curtains, tied with ribbons
    f'<path d="M1.2 4 Q5.6 3 6.2 6 Q4 13 7 20 Q3.6 21 1.2 24 Z" {s(T["CURTAIN"])}/>',
    f'<path d="M28.8 4 Q24.4 3 23.8 6 Q26 13 23 20 Q26.4 21 28.8 24 Z" {s(T["CURTAIN"])}/>',
    *([f'<path d="M2.4 6 Q4.4 11 3.6 18 M27.6 6 Q25.6 11 26.4 18" fill="none" stroke="{LACE_HOLE}" stroke-width="0.35" stroke-dasharray="0.4 0.6"/>',
       lace(0.6, 3.6, 28.8, 0.6),                                # valance
       bow(5.6, 16.4, 3.2, PINK3), bow(24.4, 16.4, 3.2, PINK3)] if J else
      [heart(5.4, 16, 0.8, PINK3), heart(24.6, 16, 0.8, PINK3)]),
    rect(0.6, 2.4, 28.8, 1.4, LAV2, 0.7),                      # rod
    *([heart(1, 3.1, 1, PINK2), heart(29, 3.1, 1, PINK2)] if J else [circ(0.9, 3.1, 0.9, BUTTER2), circ(29.1, 3.1, 0.9, BUTTER2)]),
]))

# clock: 14 x 16 cat clock with an analog face; the hands are separate files, one per angle,
# laid over the face (clock/h_<0..47>.svg every 15 minutes, clock/m_<0..59>.svg every minute).
import math
write("clock", 14, 16, "".join([
    f'<path d="M2 4.6 L2.6 0.6 L5.6 3 Z" {s(LAV2)}/>', f'<path d="M12 4.6 L11.4 0.6 L8.4 3 Z" {s(LAV2)}/>',
    circ(7, 8.4, 6.4, LAV2), circ(7, 8.4, 5, CREAM),
    *[circ(7 + 4.1 * math.sin(k * math.pi / 6), 8.4 - 4.1 * math.cos(k * math.pi / 6), 0.45 if k % 3 == 0 else 0.25,
           PINK3 if k % 3 == 0 else LAV3, False) for k in range(12)],
    f'<path d="M6 15.6 q1 -1.6 2 0" {s(LAV2)}/>',
    bow(7, 1.8, 4, PINK2) if J else "",
]))
os.makedirs(f"{OUT}/clock", exist_ok=True)
def hand(name, angle, length, width, colour):
    x, y = 7 + length * math.sin(angle), 8.4 - length * math.cos(angle)
    open(f"{OUT}/clock/{name}.svg", "w").write(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 14 16" width="112" height="128">'
        f'<path d="M7 8.4 L{x:.2f} {y:.2f}" stroke="{colour}" stroke-width="{width}" stroke-linecap="round"/>'
        f'<circle cx="7" cy="8.4" r="0.7" fill="{PINK3}"/></svg>')
for k in range(48): hand(f"h_{k}", k * math.pi / 24, 2.6, 0.9, INK)
for k in range(60): hand(f"m_{k}", k * math.pi / 30, 3.9, 0.55, LAV3)

# calendar: 13 x 16, the clock's size (drawn at the clock's scale, at the same height). The
# page is x 1.4 to 11.6: a header band y 3.4 to 7 (the month goes there), then the paper (the
# day, then the weekday; scene.js writes them). Each theme dresses it differently: bunny ears
# (pastel), a big bow over a black header with lace (jirai), bat wings and a rose (gothic).
if G:
    cal_head, cal_top, cal_extra = PINK2, "".join([
        f'<path d="M1.6 3.8 Q0.6 2.2 0.1 3.4 L0.3 6.8 Q0.8 6 1.1 6.9 Q1.3 6.1 1.6 6.8 Z" {s(LAV)}/>',
        f'<path d="M11.4 3.8 Q12.4 2.2 12.9 3.4 L12.7 6.8 Q12.2 6 11.9 6.9 Q11.7 6.1 11.4 6.8 Z" {s(LAV)}/>',
        cross(6.5, 1.9, 2.8, BUTTER),
    ]), rose(10.3, 14.3, 0.9, PINK3) + lace(1.4, 7, 10.2, 0.4)
elif J:
    cal_head, cal_top, cal_extra = LAV2, bow(6.5, 2.3, 6.4, PINK2, tails=False), lace(1.4, 7, 10.2, 0.4) + heart(10.4, 14.4, 0.6, PINK3)
else:
    # (no transform: Herdr's SVG drawing skipped rotated shapes)
    ear = lambda cx, tilt: (f'<ellipse cx="{cx}" cy="2.6" rx="1.25" ry="2.5" {s(CREAM)}/>'
                            f'<ellipse cx="{cx}" cy="2.7" rx="0.6" ry="1.7" fill="{PINK2}"/>')
    cal_head, cal_top, cal_extra = PINK2, ear(4.2, -12) + ear(8.8, 12), heart(10.4, 14.4, 0.6, PINK2)
write("calendar", 13, 16, "".join([
    "" if J and not G else cal_top,  # behind the page (the jirai bow goes on top instead)
    rect(1.4, 3.4, 10.2, 12.2, CREAM, 1.2),
    f'<path d="M1.4 7 V4.6 a1.2 1.2 0 0 1 1.2 -1.2 h7.8 a1.2 1.2 0 0 1 1.2 1.2 V7 Z" {s(cal_head)}/>',
    circ(4, 3.5, 0.45, CREAM2), circ(9, 3.5, 0.45, CREAM2),
    f'<path d="M11.6 13.6 L9.6 15.6 L11.6 15.6 Z" fill="{CREAM2}"/>',  # a page curl
    cal_extra,
    cal_top if J and not G else "",  # the bow over the header
]))

# bunting: a 24 x 5 tile of pastel flags, repeated along the top of the wall
if G:  # a silver lace garland, a wine bow and a cross on every tile
    write("bunting", 24, 5, "".join([
        f'<path d="M0 0.3 H24 V1.4 H0 Z" fill="{LAV2}"/>',
        lace(0, 1.3, 24, 0.6),
        bow(6, 1.6, 4.2, PINK2), cross(18, 2.6, 3, BUTTER),
    ]))
elif J:  # a black lace garland, a pink bow on every tile
    write("bunting", 24, 5, "".join([
        f'<path d="M0 0.3 H24 V1.4 H0 Z" fill="{LAV2}"/>',
        lace(0, 1.3, 24, 0.6, LAV2),
        bow(12, 1.6, 4.6, PINK2),
    ]))
else:
    write("bunting", 24, 5, "".join([
        f'<path d="M0 0.6 Q12 2.2 24 0.6" fill="none" stroke="{INK}" stroke-width="0.3"/>',
        *[f'<path d="M{x} {0.9 + 0.5 * (1 - abs(x + 2 - 12) / 12)} h4 l-2 4 Z" {s(c)}/>'
          for x, c in [(1, PINK2), (7, MINT2), (13, BUTTER2), (19, LAV2)]],
    ]))

# wallpaper tile 16 x 16 and floor tile 32 x 8
if G:  # dark damask: faint diamonds, small crosses and roses
    write("wallpaper", 16, 16, "".join([
        f'<rect width="16" height="16" fill="{WALL}"/>',
        f'<path d="M8 0 L16 8 L8 16 L0 8 Z" fill="none" stroke="#2e2439" stroke-width="0.4"/>',
        f'<path d="M7.5 5.6 h1 v1.2 h1.2 v1 h-1.2 v2.6 h-1 v-2.6 h-1.2 v-1 h1.2 Z" fill="#30253d"/>',
        circ(0, 0, 0.9, "#3d2436", False), circ(16, 0, 0.9, "#3d2436", False), circ(0, 16, 0.9, "#3d2436", False), circ(16, 16, 0.9, "#3d2436", False),
    ]))
    # dark checkerboard, low contrast
    write("floor", 32, 8, "".join(
        [f'<rect width="32" height="8" fill="#2c2236"/>'] +
        [f'<rect x="{x}" y="{y}" width="4" height="4" fill="#382c44"/>' for y in (0, 4) for x in range(0 if y == 0 else 4, 32, 8)]))
    write("rug", 40, 5, lace(1, 2.5, 38, 0.7) + f'<ellipse cx="20" cy="2.5" rx="19" ry="2.2" {s(PINK2)}/>'
          f'<ellipse cx="20" cy="2.5" rx="15.6" ry="1.4" fill="none" stroke="{LACE}" stroke-width="0.4" stroke-dasharray="1 0.8"/>'
          + cross(20, 2.4, 2, BUTTER))
elif J:  # pink with thin stripes, little black bows and hearts
    write("wallpaper", 16, 16, "".join([
        f'<rect width="16" height="16" fill="{WALL}"/>',
        f'<path d="M0.5 0 V16 M8.5 0 V16" stroke="#ffe0ea" stroke-width="0.5"/>',
        bow(4.5, 4.5, 2, "#c99aac", tails=False).replace(f'stroke="{INK}"', 'stroke="none"'),
        heart(12.5, 12, 0.7, "#ffd0de", False),
        circ(12.5, 4.5, 0.3, "#f6c4d4", False), circ(4.5, 12, 0.3, "#f6c4d4", False),
    ]))
    # a soft checkerboard: two light pinks, 4-unit squares, two rows a tile. Low contrast, so
    # the black furniture and the girls stand out against it.
    write("floor", 32, 8, "".join(
        [f'<rect width="32" height="8" fill="#fbe1ea"/>'] +
        [f'<rect x="{x}" y="{y}" width="4" height="4" fill="#f5cdda"/>' for y in (0, 4) for x in range(0 if y == 0 else 4, 32, 8)]))
    write("rug", 40, 5, lace(1, 2.5, 38, 0.7) + f'<ellipse cx="20" cy="2.5" rx="19" ry="2.2" {s(PINK)}/>'
          f'<ellipse cx="20" cy="2.5" rx="15.6" ry="1.4" fill="none" stroke="{LACE}" stroke-width="0.5" stroke-dasharray="1 0.8"/>'
          + heart(20, 2.4, 0.8, PINK3, False))
else:
    write("wallpaper", 16, 16, "".join([
        f'<rect width="16" height="16" fill="{WALL}"/>',
        star(4, 4, 0.9, "#ffe3ec", False), heart(12, 12, 0.8, "#ffe3ec", False),
        circ(12, 4, 0.35, "#f6d7e1", False), circ(4, 12, 0.35, "#f6d7e1", False),
    ]))
    write("floor", 32, 8, "".join([
        f'<rect width="32" height="8" fill="{WOOD}"/>',
        f'<path d="M0 7.8 H32 M10 0 V7.8 M26 0 V7.8" stroke="{WOOD2}" stroke-width="0.35"/>',
        f'<path d="M3 3.2 h4" stroke="#f7dcbd" stroke-width="0.5" stroke-linecap="round"/>',
        f'<path d="M15 5 h6" stroke="#f7dcbd" stroke-width="0.5" stroke-linecap="round"/>',
    ]))
    # rug under the couch area: 40 x 5
    write("rug", 40, 5, f'<ellipse cx="20" cy="2.5" rx="19.6" ry="2.3" {s(LAV)}/>'
          f'<ellipse cx="20" cy="2.5" rx="16" ry="1.5" fill="none" stroke="{CREAM}" stroke-width="0.5" stroke-dasharray="1 0.8"/>')
# a lace trim tile for the wainscot rail, 8 x 2 (only drawn in themes that have lace)
write("lace", 8, 2, lace(0, 0.2, 8, 0.5, T.get("RAIL_LACE")))

# cat: 14 x 11, facing right. A chubby orange tabby: round body, white belly and muzzle.
# The cat: an orange tabby in the pastel office, a white cat with pink stripes in jirai-kei,
# a silver-lilac one in gothic (a dark cat would vanish on the dark floor and furniture).
CAT, CAT2, CAT3, BELLY = {
    "pastel": ("#ffb15c", "#f08a3c", "#ffd29a", "#fff4e4"),
    "jirai": ("#fffafc", "#f6a9c2", "#ffe3ec", "#ffffff"),
    "gothic": ("#cfc6dc", "#8f80a8", "#e4dfeb", "#f2eef6"),
}[THEME]
def cat_head(x, y):
    return "".join([
        f'<path d="M{x - 2.8} {y - 0.8} L{x - 2.5} {y - 3.6} L{x - 0.5} {y - 2.3} Z" {s(CAT)}/>',
        f'<path d="M{x + 2.8} {y - 0.8} L{x + 2.5} {y - 3.6} L{x + 0.5} {y - 2.3} Z" {s(CAT)}/>',
        f'<path d="M{x - 2.2} {y - 1.4} L{x - 2.1} {y - 2.9} L{x - 1.1} {y - 2.2} Z" fill="{PINK2}"/>',
        f'<path d="M{x + 2.2} {y - 1.4} L{x + 2.1} {y - 2.9} L{x + 1.1} {y - 2.2} Z" fill="{PINK2}"/>',
        f'<ellipse cx="{x}" cy="{y}" rx="3.4" ry="2.7" {s(CAT)}/>',
        f'<path d="M{x - 0.9} {y - 2.6} v1.1 M{x} {y - 2.7} v1.3 M{x + 0.9} {y - 2.6} v1.1" stroke="{CAT2}" stroke-width="0.4" stroke-linecap="round"/>',
        f'<ellipse cx="{x + 0.1}" cy="{y + 1}" rx="1.5" ry="1" fill="{BELLY}"/>',
        circ(x - 1.2, y - 0.1, 0.38, INK, False), circ(x + 1.4, y - 0.1, 0.38, INK, False),
        circ(x - 1.1, y - 0.25, 0.12, "#ffffff", False), circ(x + 1.5, y - 0.25, 0.12, "#ffffff", False),
        circ(x - 2.1, y + 0.8, 0.45, PINK2, False), circ(x + 2.3, y + 0.8, 0.45, PINK2, False),
        f'<path d="M{x - 0.4} {y + 0.8} q0.4 0.45 0.5 0 q0.1 0.45 0.5 0" fill="none" stroke="{INK}" stroke-width="0.22" stroke-linecap="round"/>',
        bow(x - 0.6, y + 2.6, 2, PINK3, tails=False) if J else "",
    ])
def tail(d):
    return (f'<path d="{d}" fill="none" stroke="{INK}" stroke-width="1.7" stroke-linecap="round"/>'
            f'<path d="{d}" fill="none" stroke="{CAT}" stroke-width="1.1" stroke-linecap="round"/>')
write("cat_sit", 14, 11, "".join([
    tail("M3.4 10.2 Q0.6 10.2 0.9 7"),
    f'<ellipse cx="6.4" cy="7.9" rx="4.4" ry="3" {s(CAT)}/>',
    f'<path d="M3.2 6.4 q0.8 0.8 0 1.8 M4.4 5.6 q0.8 0.9 0 2" fill="none" stroke="{CAT2}" stroke-width="0.45" stroke-linecap="round"/>',
    f'<ellipse cx="7.6" cy="8.4" rx="2" ry="2.1" fill="{BELLY}"/>',
    f'<ellipse cx="6.6" cy="10.5" rx="1.1" ry="0.55" {s(CAT3)}/>', f'<ellipse cx="9" cy="10.5" rx="1.1" ry="0.55" {s(CAT3)}/>',
    cat_head(8.2, 4.2),
]), turns=True)
write("cat_sleep", 14, 11, "".join([
    tail("M2.2 10.2 Q0.6 9.6 1.4 8"),
    f'<ellipse cx="6.6" cy="8.3" rx="5.8" ry="2.6" {s(CAT)}/>',
    f'<path d="M3.4 6.2 q0.7 0.9 0 1.8 M5 5.8 q0.7 0.9 0 1.9 M6.6 5.8 q0.7 0.9 0 1.8" fill="none" stroke="{CAT2}" stroke-width="0.45" stroke-linecap="round"/>',
    f'<path d="M9.6 6.8 L9.7 4.8 L11 5.9 Z" {s(CAT)}/>', f'<path d="M12.6 7 L13 5 L11.6 5.9 Z" {s(CAT)}/>',
    f'<ellipse cx="11.2" cy="8" rx="2.6" ry="2.1" {s(CAT)}/>',
    f'<ellipse cx="11.4" cy="8.9" rx="1.3" ry="0.8" fill="{BELLY}"/>',
    f'<path d="M9.9 7.8 q0.45 0.35 0.9 0 M11.6 7.8 q0.45 0.35 0.9 0" fill="none" stroke="{INK}" stroke-width="0.24" stroke-linecap="round"/>',
    circ(12.9, 8.6, 0.4, PINK2, False),
    f'<ellipse cx="9" cy="10.4" rx="1.1" ry="0.5" {s(CAT3)}/>',
]), turns=True)
def cat_walk(k):
    legs = [(4.2, 0.5), (9, -0.5)] if k == 0 else [(4.2, -0.5), (9, 0.5)]
    return "".join([
        *[f'<path d="M{x} 8.6 L{x + d} 10.4" stroke="{INK}" stroke-width="1.5" stroke-linecap="round"/>'
          f'<path d="M{x} 8.6 L{x + d} 10.4" stroke="{CAT}" stroke-width="0.9" stroke-linecap="round"/>' for x, d in legs],
        tail("M2.4 7 Q0.4 5.4 1.2 3.4"),
        f'<ellipse cx="6.6" cy="7.3" rx="4.8" ry="2.9" {s(CAT)}/>',
        f'<path d="M4.4 4.8 q0.7 0.9 0 1.9 M6 4.5 q0.7 0.9 0 2 M7.6 4.6 q0.7 0.9 0 1.9" fill="none" stroke="{CAT2}" stroke-width="0.45" stroke-linecap="round"/>',
        f'<ellipse cx="7" cy="8.9" rx="3.2" ry="1.1" fill="{BELLY}"/>',
        cat_head(10.6, 4.9),
    ])
write("cat_walk_0", 14, 11, cat_walk(0), turns=True)
write("cat_walk_1", 14, 11, cat_walk(1), turns=True)

# interns: stool 9 x 7 (seat top at 7, like the chair) and a laptop on the lap 6 x 4
write("stool", 9, 7, rect(0.4, 0.4, 8.2, 1.6, MINT2, 0.8) + rect(1.4, 2, 1, 4.8, CREAM2, 0.3) + rect(6.6, 2, 1, 4.8, CREAM2, 0.3))
write("laptop", 6, 4, f'<path d="M0.4 3.4 h4.6 L5.6 0.4 L1.2 0.4 Z" {s(LAV)}/>' + heart(3.2, 1.9, 0.5, PINK2))

print("wrote", len(os.listdir(OUT)), "files to", OUT)
