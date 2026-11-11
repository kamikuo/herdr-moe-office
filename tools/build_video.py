"""Character videos -> sprite frames for the moe-office mod.

Usage: build_video.py <character>   (a key of CHARS)
Input : art-src/video/<character>/setA.mp4, setB.mp4 (1280x720, 24 fps, character facing
        right, on white or on a green screen).
Output: mods/moe-office/chars/<character>/<anim>[_l]{.png,_hair.svg,_shade.png} and char.js (the
        manifest). _l: mirrored (she faces left). Each frame is written on its own first, then
        pack_sheets.py puts each action's frames into one sheet per layer and facing.

Each action is a loop cut out of one video (CHARS below). The background is knocked out,
edge pixels get the background colour taken out, and the size is matched across the two
videos by the standing height. Each frame is split into three layers so the mod can give
every coworker her own hair colour when it draws her (split() below):
- .png: everything but the hair, eyes and ribbon (the pink parts).
- _hair.svg: where those are, as a mask the mod fills with her colour.
- _shade.png: black (shadow) and white (shine) on top of that colour.
"""
import sys, os, json, subprocess, tempfile, base64, io
import numpy as np
from PIL import Image
from scipy import ndimage as nd

NAME = sys.argv[1]
SRC, OUT = f"art-src/video/{NAME}", f"mods/moe-office/chars/{NAME}"
FPS = 24
# Real-ESRGAN (github.com/xinntao/Real-ESRGAN, the realesrgan-ncnn-vulkan macOS release),
# unpacked into .tools/realesrgan/ (not in git).
ESRGAN = ".tools/realesrgan/realesrgan-ncnn-vulkan"
STAND = 220  # standing height in output px (head top to soles)
# Per character:
# - bg: "white" or "green" (a chroma-key green screen).
# - actions: anim -> (video, first frame, loop end (exclusive), take every Nth frame), 1-based.
#   Pick the loop where the first frame and the end frame look most alike.
# - flip: actions she does facing left in the video; they are mirrored to face right.
# - speed: actions played faster (or slower) than the video.
# - pingpong: actions played forwards then backwards (a sway from one side to the other and
#   back), so they need no matching end frame. Start and end where she turns around.
# - standing: frames where she stands still on both feet with her hands below her head,
#   to measure the floor and her height.
CHARS = {
    "jirai": {  # the second try: same girl, a rounder style, on a green screen
        "bg": "green",
        "actions": {
            "idle": ("setA", 10, 28, 2), "walk": ("setA", 95, 116, 2), "typing": ("setA", 202, 229, 2),
            "blocked": ("setB", 25, 41, 2), "cheer": ("setB", 79, 132, 2), "sleep": ("setB", 193, 227, 2),
        },
        "standing": {"setA": range(15, 33), "setB": range(1, 5)},
        "flip": {"typing"},  # she typed facing left in the video
        "speed": {"cheer": 1.35, "idle": 0.75},  # cheer felt slow; idle is a slow sway
        "pingpong": {"idle"},
    },
    "intern": {  # one ponytail, sailor uniform
        "bg": "green",
        "actions": {
            "idle": ("setA", 2, 14, 2), "walk": ("setA", 97, 119, 2), "typing": ("setA", 210, 230, 2),
            "blocked": ("setB", 43, 57, 2), "cheer": ("setB", 81, 143, 2), "sleep": ("setB", 206, 238, 2),
        },
        "standing": {"setA": range(15, 33), "setB": range(1, 5)},
        "speed": {"cheer": 1.35, "idle": 0.75},
        "pingpong": {"idle"},
    },
    "designer-cute": {  # long straight hair, big bow, blue dress
        "bg": "green",
        "actions": {
            "idle": ("setA", 10, 24, 2), "walk": ("setA", 72, 92, 2), "typing": ("setA", 204, 231, 2),
            "blocked": ("setB", 25, 47, 2), "cheer": ("setB", 81, 145, 2), "sleep": ("setB", 180, 213, 2),
        },
        "standing": {"setA": range(15, 33), "setB": range(1, 5)},
        "flip": {"typing"},
        "speed": {"cheer": 1.35, "idle": 0.75},
        "pingpong": {"idle"},
    },
    "engineer-hoodie": {  # side ponytail, hoodie, headphones
        "bg": "green",
        "actions": {
            "idle": ("setA", 10, 28, 2), "walk": ("setA", 103, 127, 2), "typing": ("setA", 161, 181, 2),
            "blocked": ("setB", 43, 65, 2), "cheer": ("setB", 78, 142, 2), "sleep": ("setB", 195, 239, 2),
        },
        "standing": {"setA": range(15, 33), "setB": range(1, 5)},
        "speed": {"cheer": 1.35, "idle": 0.75},
        "pingpong": {"idle"},
    },
    "wavy-blouse": {  # long wavy hair, white blouse, lilac skirt
        "bg": "green",
        "actions": {
            "idle": ("setA", 14, 32, 2), "walk": ("setA", 98, 121, 2), "typing": ("setA", 196, 219, 2),
            "blocked": ("setB", 31, 46, 2), "cheer": ("setB", 86, 144, 2), "sleep": ("setB", 193, 239, 2),
        },
        "standing": {"setA": range(15, 33), "setB": range(1, 5)},
        "speed": {"cheer": 1.35, "idle": 0.75},
        "pingpong": {"idle"},
    },
    "twintail-blazer": {  # twin tails, navy school blazer, a cat mug while idle
        "bg": "green",
        "actions": {
            "idle": ("setA", 16, 34, 2), "walk": ("setA", 110, 133, 2), "typing": ("setA", 208, 229, 2),
            "blocked": ("setB", 48, 62, 2), "cheer": ("setB", 78, 142, 2), "sleep": ("setB", 189, 229, 2),
        },
        "standing": {"setA": range(15, 33), "setB": range(1, 5)},
        "speed": {"cheer": 1.35, "idle": 0.75},
        "pingpong": {"idle"},
    },
    "bob-jacket": {  # short bob, lilac jacket, leg warmers
        "bg": "green",
        "actions": {
            "idle": ("setA", 13, 31, 2), "walk": ("setA", 97, 120, 2), "typing": ("setA", 187, 206, 2),
            "blocked": ("setB", 36, 51, 2), "cheer": ("setB", 66, 122, 2), "sleep": ("setB", 187, 216, 2),
        },
        "standing": {"setA": range(15, 33), "setB": range(1, 5)},
        "speed": {"cheer": 1.35, "idle": 0.75},
        "pingpong": {"idle"},
    },
}
CFG = CHARS[NAME]
ACTIONS, STANDING = CFG["actions"], CFG["standing"]
# The pink parts (hair, eyes, ribbon): hue PINK +- PINK_HUE (fading out over 6 more degrees),
# chroma above 0.10. Her skin (hue 5-27) and blush (355-10) stay out. HAIR: the hair's main
# colour; the mod's "pink" is this colour, so pink looks like the video.
PINK, PINK_HUE = 343, 8
HAIR = np.array([246, 166, 190]) / 255
# Eye whites (kept): at most EYE_MAX px, within HEAD px of her top. In video px (she is ~640 tall).
EYE_MAX, HEAD = 800, 150


def frames(video, wanted):
    """{frame number: RGB array} for the wanted frames of a video, cleaned up and doubled in
    size by Real-ESRGAN (its anime video model): it removes the video's compression noise and
    the colour smeared over the edges, and sharpens the lines."""
    with tempfile.TemporaryDirectory() as tmp:
        os.makedirs(f"{tmp}/in"); os.makedirs(f"{tmp}/out")
        subprocess.run(["ffmpeg", "-v", "error", "-i", f"{SRC}/{video}.mp4", f"{tmp}/all_%03d.png"], check=True)
        for i in wanted: os.rename(f"{tmp}/all_{i:03d}.png", f"{tmp}/in/{i:03d}.png")
        print(f"{video}: Real-ESRGAN on {len(wanted)} frames")
        subprocess.run([ESRGAN, "-i", f"{tmp}/in", "-o", f"{tmp}/out", "-n", "realesr-animevideov3",
                        "-s", "2", "-m", os.path.dirname(ESRGAN) + "/models"], check=True, capture_output=True)
        return {i: np.asarray(Image.open(f"{tmp}/out/{i:03d}.png").convert("RGB")) for i in wanted}


def cutout(a):
    return cutout_green(a) if CFG["bg"] == "green" else cutout_white(a)


def keep_body(fg):
    """Drop specks: keep the pieces at least 2% the size of the biggest."""
    lab, m = nd.label(fg)
    s = nd.sum(fg, lab, range(1, m + 1))
    return np.isin(lab, 1 + np.where(s >= s.max() * 0.02)[0])


def unmix(ai, fg, alpha):
    """Edge pixels with background mixed in (alpha below 1) take the colour of the nearest
    solid pixel; alpha says how much of her is in them. Opaque edge pixels keep their own
    colour: they are her outline."""
    solid = nd.binary_erosion(fg, iterations=2)
    _, (iy, ix) = nd.distance_transform_edt(~solid, return_indices=True)
    band = fg & ~solid & (alpha < 0.99)
    rgb = np.where(band[..., None], ai[iy, ix], ai)
    alpha = np.where(band, alpha, fg.astype(float))
    return np.dstack([rgb, alpha * 255]).astype(np.uint8)


def cutout_green(a):
    """RGBA with the green screen removed. Greenness (G above max(R, B)) of the screen is
    measured on the border; less green = more of her. Nothing on her is green."""
    ai = a.astype(float)
    gn = ai[..., 1] - np.maximum(ai[..., 0], ai[..., 2])
    edge = np.r_[ai[0], ai[-1], ai[:, 0], ai[:, -1]]
    screen_rgb = np.median(edge, 0)
    screen = np.median(np.r_[gn[0], gn[-1], gn[:, 0], gn[:, -1]])
    # 0.7: Real-ESRGAN leaves a lighter green ring around her; it counts as screen.
    alpha = np.clip((screen * 0.7 - gn) / (screen * 0.7 - 15), 0, 1)
    fg = keep_body(alpha > 0.5)
    fg = nd.binary_dilation(fg, iterations=2) & (alpha > 0.02)
    alpha = alpha * fg
    # Unmix: pixel = alpha * her colour + (1 - alpha) * screen, solved for her colour.
    # Opaque pixels (her outline included) stay as they are.
    rgb = np.clip((ai - (1 - alpha[..., None]) * screen_rgb) / np.maximum(alpha, 0.05)[..., None], 0, 255)
    # Despill: no pixel of her is greener than it is red or blue.
    rgb[..., 1] = np.minimum(rgb[..., 1], np.maximum(rgb[..., 0], rgb[..., 2]))
    return np.dstack([rgb, alpha * 255]).round().astype(np.uint8)


def cutout_white(a):
    """RGBA with the white background removed and the white taken out of edge pixels."""
    ai = a.astype(int)
    white = ai.min(2) > 232
    dark = ai.max(2) < 90
    lab, n = nd.label(white)
    objs = nd.find_objects(lab)
    sizes = nd.sum(white, lab, range(1, n + 1))
    bg = set(np.unique(np.r_[lab[0], lab[-1], lab[:, 0], lab[:, -1]])) - {0}
    # Enclosed white is a gap (between hair, arms, body and legs) unless it is an eye white:
    # small, in the head (the top HEAD px of her), with a dark outline around it.
    top = np.where((~np.isin(lab, list(bg))).any(1))[0].min()
    for k in range(1, n + 1):
        if k in bg or sizes[k - 1] < 150: continue
        sl = tuple(slice(max(0, s.start - 5), s.stop + 5) for s in objs[k - 1])
        cy = (objs[k - 1][0].start + objs[k - 1][0].stop) / 2
        if sizes[k - 1] > EYE_MAX or cy > top + HEAD: bg.add(k); continue
        r = lab[sl] == k
        ring = nd.binary_dilation(r, iterations=4) & ~r & ~white[sl]
        if dark[sl][ring].mean() < 0.06: bg.add(k)
    fg = keep_body(~np.isin(lab, list(bg)))
    # Alpha from how much white is mixed in, against the nearest solid pixel's colour.
    solid = nd.binary_erosion(fg, iterations=2)
    _, (iy, ix) = nd.distance_transform_edt(~solid, return_indices=True)
    F = ai[iy, ix].astype(float)
    alpha = np.clip(((255 - ai) / np.maximum(255 - F, 1)).max(2), 0, 1)
    return unmix(ai, fg, alpha)


def measure(cuts):
    """Floor y, head-top y and centre x of a standing pose (medians over frames)."""
    floors, tops, cxs = [], [], []
    for c in cuts:
        m = c[..., 3] > 128
        ys = np.where(m.any(1))[0]
        floors.append(ys.max()); tops.append(ys.min())
        legs = m[int(ys.max() - 0.3 * (ys.max() - ys.min())):]  # lower 30%: legs and skirt hem
        cxs.append(np.where(legs.any(0))[0].mean())
    return float(np.median(floors)), float(np.median(tops)), float(np.median(cxs))


def luma(a):
    return a[..., 0] * 0.299 + a[..., 1] * 0.587 + a[..., 2] * 0.114


def split(rgba):
    """One cut frame -> (base RGBA, hair mask 0..1, shade RGBA), all float 0..1.

    Drawn in order, with the mask filled with colour T: inside the hair the result is T made
    darker by the shade's black (T * (1 - s)) or lighter by its white, by how much darker or
    lighter that pixel is than HAIR. Pixels partly hair (the edge against the outline) keep
    the rest of their colour in the base."""
    a = rgba[..., :3].astype(float) / 255
    al = rgba[..., 3].astype(float) / 255
    mx, mn = a.max(2), a.min(2)
    ch = mx - mn
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    h = np.where(mx == r, ((g - b) / (ch + 1e-9)) % 6,
                 np.where(mx == g, (b - r) / (ch + 1e-9) + 2, (r - g) / (ch + 1e-9) + 4)) * 60
    d = (h - PINK + 180) % 360 - 180
    w = np.clip((PINK_HUE + 6 - np.abs(d)) / 6, 0, 1) * np.clip((ch - 0.10) / 0.08, 0, 1)
    y, y0 = luma(a), luma(HAIR)
    dark = np.clip(1 - y / y0, 0, 1)
    shine = np.clip((y - y0) / (1 - y0), 0, 1)
    # Hair as it would look at this pixel, to take it out of the partly-hair pixels.
    hp = np.where((y < y0)[..., None], HAIR * (1 - dark)[..., None], HAIR + (1 - HAIR) * shine[..., None])
    rest = np.clip((a - w[..., None] * hp) / np.maximum(1 - w, 0.02)[..., None], 0, 1)
    base = np.dstack([np.where((w > 0.98)[..., None], 0, rest), al * (1 - w)])
    mask = al * w
    grey = (shine > dark).astype(float)
    shade = np.dstack([grey, grey, grey, mask * np.maximum(dark, shine)])
    return base, mask, shade


def shrink(rgba, W, H):
    """Float RGBA -> PIL RGBA at W x H (premultiplied, so the edges get no dark fringe)."""
    im = Image.fromarray((rgba * 255).round().astype(np.uint8), "RGBA")
    return im.convert("RGBa").resize((W, H), Image.LANCZOS).convert("RGBA")


def levels(x):
    """0..1 -> 0..255 in 16 steps: the masks need no more, and the PNG gets three times smaller."""
    return (np.round(np.clip(x, 0, 1) * 15) * 17).astype(np.uint8)


def mask_svg(mask, path):
    """The mask as an SVG with the mask inside as a PNG: the mod draws it with svg(), which
    fills its shape with one colour."""
    buf = io.BytesIO()
    a = Image.fromarray(levels(mask))
    Image.merge("LA", (Image.new("L", a.size, 255), a)).save(buf, "PNG", optimize=True)
    data = base64.b64encode(buf.getvalue()).decode()
    w, h = a.size
    with open(path, "w") as f:
        f.write(f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{w}" height="{h}" viewBox="0 0 {w} {h}">'
                f'<image width="{w}" height="{h}" xlink:href="data:image/png;base64,{data}"/></svg>')


def main():
    by_video = {}
    for name, (v, a, b, step) in ACTIONS.items():
        by_video.setdefault(v, set()).update(range(a, b, step))
    for v, rng in STANDING.items():
        by_video.setdefault(v, set()).update(rng)
    raw = {v: frames(v, sorted(w)) for v, w in by_video.items()}
    cuts = {v: {i: cutout(f) for i, f in fs.items()} for v, fs in raw.items()}
    geo = {}
    for v, rng in STANDING.items():
        floor, top, cx = measure([cuts[v][i] for i in rng])
        geo[v] = (floor, cx, STAND / (floor - top))
        print(f"{v}: floor {floor:.0f}, height {floor - top:.0f}px, centre {cx:.0f}, scale {geo[v][2]:.3f}")

    os.makedirs(OUT, exist_ok=True)
    manifest = {"stand": STAND, "anim": {}}
    for name, (v, a, b, step) in ACTIONS.items():
        floor, cx, k = geo[v]
        seq = [cuts[v][i] for i in range(a, b, step)]
        m = np.zeros(seq[0].shape[:2], bool)
        for c in seq: m |= c[..., 3] > 0
        ys, xs = np.where(m)
        x0, x1 = xs.min() - 2, xs.max() + 3
        y0, y1 = ys.min() - 2, max(ys.max() + 3, int(floor) + 3)
        W, H = round((x1 - x0) * k), round((y1 - y0) * k)
        flip = name in CFG.get("flip", ())
        if flip:
            fw = seq[0].shape[1]
            seq = [c[:, ::-1] for c in seq]; x0, x1, cx = fw - x1, fw - x0, fw - cx
        anchor = {"cx": round(float(cx - x0) * k, 1), "feet": round(float(floor - y0) * k, 1)}
        manifest["anim"][name] = {"n": len(seq), "ms": round(step * 1000 / FPS / CFG.get("speed", {}).get(name, 1)), "w": W, "h": H, **anchor,
                                  **({"pingpong": True} if name in CFG.get("pingpong", ()) else {})}
        for i, c in enumerate(seq):
            base, mask, shade = split(c[y0:y1, x0:x1])
            base, shade = shrink(base, W, H), shrink(shade, W, H)
            mask = np.asarray(Image.fromarray((mask * 255).round().astype(np.uint8)).resize((W, H), Image.LANCZOS)) / 255
            for suffix, flip_x in (("", False), ("_l", True)):
                f = f"{OUT}/{name}_{i}{suffix}"
                b, s_ = (base.transpose(Image.FLIP_LEFT_RIGHT), shade.transpose(Image.FLIP_LEFT_RIGHT)) if flip_x else (base, shade)
                # 256 colours: a quarter of the size, no visible difference at this scale.
                # No dithering: it breaks thin lines into specks.
                b.quantize(256, method=Image.Quantize.FASTOCTREE, dither=Image.Dither.NONE).save(f"{f}.png", optimize=True)
                # Black or white at 16 strengths: 32 colours, so a palette PNG holds it exactly.
                grey = np.where(np.asarray(s_.getchannel("R")) > 127, 255, 0).astype(np.uint8)
                alpha = levels(np.asarray(s_.getchannel("A")) / 255)
                Image.fromarray(np.dstack([grey, grey, grey, alpha]), "RGBA").quantize(
                    32, method=Image.Quantize.FASTOCTREE, dither=Image.Dither.NONE).save(f"{f}_shade.png", optimize=True)
                mask_svg(mask[:, ::-1] if flip_x else mask, f"{f}_hair.svg")
        print(f"{name}: {len(seq)} frames, {W}x{H}, {anchor}")
    with open(f"{OUT}/char.js", "w") as f:
        f.write("// Generated by tools/build_video.py\nexport const CHAR = " + json.dumps(manifest, indent=1) + ";\n")
    subprocess.run([sys.executable, "-I", "tools/pack_sheets.py", NAME], check=True)


main()
