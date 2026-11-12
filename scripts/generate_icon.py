#!/usr/bin/env python3
"""Generate the Foxgram app icon.

Original geometric fox-face artwork (flat polygons, no Telegram/Nekogram
artwork, no text), defined once as polygon geometry in a 1024x1024 canvas
and emitted in the two forms the pinned Telegram-iOS 12.10 build uses:

1. `assets/icon/Telegram.icon/` — an Xcode 26 Icon Composer package
   (icon.json + SVG layers), structurally modelled on the stock
   `Telegram.icon` at the pinned commit. This is what the Bazel build
   actually compiles: Telegram/BUILD takes the main app icon from the
   `Telegram-iOS/Telegram.icon` filegroup (composer_icon_folders).
   The workflow replaces that directory with this package.

2. `assets/icon/AppIcon.appiconset/` — a classic PNG appiconset whose
   filenames and pixel sizes mirror the stock
   `DefaultAppIcon.xcassets/AppIconLLC.appiconset` at the pinned commit
   (Contents.json included verbatim in structure). Kept as the rendered
   record of the artwork and for any non-Bazel use.

Run: python3 scripts/generate_icon.py
"""

import json
import os
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
ICON_DIR = os.path.join(REPO, "assets", "icon", "Telegram.icon")
PNG_DIR = os.path.join(REPO, "assets", "icon", "AppIcon.appiconset")

CANVAS = 1024

# --- Palette ---------------------------------------------------------------
BG_TOP = (255, 168, 61)      # #FFA83D
BG_BOTTOM = (251, 126, 20)   # #FB7E14
EAR_OUTER = (232, 100, 12)   # #E8640C
EAR_INNER = (255, 217, 174)  # #FFD9AE
FACE = (255, 244, 224)       # #FFF4E0
CAP = (240, 127, 19)         # #F07F13
CHEEK = (255, 231, 196)      # #FFE7C4
DARK = (46, 42, 38)          # #2E2A26 (eyes, nose)

# --- Fox geometry (1024x1024, y down, drawn in order) ----------------------
# Each entry: (fill, [(x, y), ...])
FOX_LAYERS = [
    # ears (outer)
    (EAR_OUTER, [(262, 452), (318, 142), (486, 318)]),
    (EAR_OUTER, [(762, 452), (706, 142), (538, 318)]),
    # ears (inner)
    (EAR_INNER, [(322, 392), (348, 232), (442, 322)]),
    (EAR_INNER, [(702, 392), (676, 232), (582, 322)]),
    # head / face (cream)
    (FACE, [(272, 420), (512, 360), (752, 420), (768, 540), (512, 818), (256, 540)]),
    # orange forehead cap
    (CAP, [(360, 398), (664, 398), (512, 545)]),
    # cheeks
    (CHEEK, [(262, 528), (512, 812), (506, 612), (396, 520), (312, 498)]),
    (CHEEK, [(762, 528), (512, 812), (518, 612), (628, 520), (712, 498)]),
    # eyes
    (DARK, [(372, 478), (462, 462), (458, 492), (378, 502)]),
    (DARK, [(652, 478), (562, 462), (566, 492), (646, 502)]),
    # nose
    (DARK, [(468, 722), (556, 722), (512, 776)]),
]

# filename -> pixel size, mirroring the stock AppIconLLC.appiconset at the
# pinned commit (verified against the actual stock PNG dimensions).
PNG_SET = {
    "BlueNotificationIcon@2x.png": 40,
    "BlueNotificationIcon@3x.png": 60,
    "Simple@58x58.png": 58,
    "Simple@87x87.png": 87,
    "Simple@80x80.png": 80,
    "BlueIcon@2x-1.png": 120,
    "BlueIcon@2x.png": 120,
    "BlueIcon@3x.png": 180,
    "BlueNotificationIcon.png": 20,
    "BlueNotificationIcon@2x-1.png": 40,
    "Simple@29x29.png": 29,
    "Simple@58x58-1.png": 58,
    "Simple@40x40-1.png": 40,
    "Simple@80x80-1.png": 80,
    "BlueIconIpad@2x.png": 152,
    "BlueIconLargeIpad@2x.png": 167,
    "Simple-iTunesArtwork.png": 1024,
}


def hex_of(rgb):
    return "#{:02X}{:02X}{:02X}".format(*rgb)


def render_png(size):
    """Full-bleed icon: orange gradient background + fox face."""
    ss = 4  # supersampling
    w = size * ss
    scale = w / CANVAS
    # vertical gradient
    grad = Image.new("RGB", (1, w))
    for y in range(w):
        t = y / max(w - 1, 1)
        grad.putpixel((0, y), tuple(
            round(BG_TOP[i] + (BG_BOTTOM[i] - BG_TOP[i]) * t) for i in range(3)
        ))
    img = grad.resize((w, w))
    draw = ImageDraw.Draw(img)
    for fill, pts in FOX_LAYERS:
        draw.polygon([(x * scale, y * scale) for x, y in pts], fill=fill)
    return img.resize((size, size), Image.LANCZOS)


def svg_path(pts):
    d = "M" + " L".join("{},{}".format(x, y) for x, y in pts) + " Z"
    return d


def write_svg_layers():
    assets = os.path.join(ICON_DIR, "Assets")
    os.makedirs(assets, exist_ok=True)
    # Fox.svg — the fox face artwork, transparent background.
    paths = "\n".join(
        '        <path d="{}" fill="{}"></path>'.format(svg_path(pts), hex_of(fill))
        for fill, pts in FOX_LAYERS
    )
    fox_svg = """<?xml version="1.0" encoding="UTF-8"?>
<svg width="1024px" height="1024px" viewBox="0 0 1024 1024" version="1.1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
    <title>Fox</title>
    <g id="Fox" stroke="none" fill="none" fill-rule="nonzero">
{paths}
    </g>
</svg>
""".format(paths=paths)
    with open(os.path.join(assets, "Fox.svg"), "w") as f:
        f.write(fox_svg)
    # Background.svg — a plain circle; its colour comes from the gradient
    # fill-specializations in icon.json (same mechanism as the stock Oval).
    bg_svg = """<?xml version="1.0" encoding="UTF-8"?>
<svg width="1024px" height="1024px" viewBox="0 0 1024 1024" version="1.1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
    <title>Background</title>
    <g id="Background" stroke="none" fill="none" fill-rule="nonzero">
        <circle fill="#000000" cx="512" cy="512" r="410.5"></circle>
    </g>
</svg>
"""
    with open(os.path.join(assets, "Background.svg"), "w") as f:
        f.write(bg_svg)


def blend_spec():
    return [
        {"value": "normal"},
        {"appearance": "dark", "value": "normal"},
    ]


def write_icon_json():
    icon = {
        "fill": "system-light",
        "groups": [
            {
                "blend-mode": "normal",
                "blur-material": 1,
                "layers": [
                    {
                        "blend-mode-specializations": blend_spec(),
                        "fill-specializations": [
                            {"appearance": "dark", "value": "automatic"},
                        ],
                        "glass": True,
                        "image-name": "Fox.svg",
                        "name": "Fox",
                        "position-specializations": [
                            {
                                "idiom": "watchOS",
                                "value": {
                                    "scale": 1.15,
                                    "translation-in-points": [0, 0],
                                },
                            }
                        ],
                    },
                    {
                        "blend-mode-specializations": blend_spec(),
                        "fill-specializations": [
                            {
                                "value": {
                                    "linear-gradient": [
                                        "display-p3:1.00000,0.65882,0.23922,1.00000",
                                        "srgb:0.98431,0.49412,0.07843,1.00000",
                                    ]
                                }
                            },
                            {
                                "appearance": "dark",
                                "value": {
                                    "automatic-gradient": "srgb:0.85098,0.36078,0.05098,1.00000"
                                },
                            },
                        ],
                        "glass": True,
                        "hidden-specializations": [
                            {"value": False},
                            {"idiom": "watchOS", "value": False},
                        ],
                        "image-name": "Background.svg",
                        "name": "Background",
                        "position-specializations": [
                            {
                                "idiom": "watchOS",
                                "value": {
                                    "scale": 2,
                                    "translation-in-points": [0, 0],
                                },
                            }
                        ],
                    },
                ],
                "lighting": "combined",
                "position-specializations": [
                    {
                        "idiom": "watchOS",
                        "value": {"scale": 1, "translation-in-points": [0, 0]},
                    }
                ],
                "shadow": {"kind": "layer-color", "opacity": 1},
                "specular": True,
                "translucency": {"enabled": False, "value": 1},
            }
        ],
        "supported-platforms": {
            "circles": ["watchOS"],
            "squares": "shared",
        },
    }
    with open(os.path.join(ICON_DIR, "icon.json"), "w") as f:
        json.dump(icon, f, indent=2)
        f.write("\n")


def write_png_set():
    os.makedirs(PNG_DIR, exist_ok=True)
    for name, size in sorted(PNG_SET.items()):
        render_png(size).save(os.path.join(PNG_DIR, name))
    # Contents.json: same image table as the stock AppIconLLC set.
    images = [
        ("BlueNotificationIcon@2x.png", "iphone", "2x", "20x20"),
        ("BlueNotificationIcon@3x.png", "iphone", "3x", "20x20"),
        ("Simple@58x58.png", "iphone", "2x", "29x29"),
        ("Simple@87x87.png", "iphone", "3x", "29x29"),
        ("Simple@80x80.png", "iphone", "2x", "40x40"),
        ("BlueIcon@2x-1.png", "iphone", "3x", "40x40"),
        ("BlueIcon@2x.png", "iphone", "2x", "60x60"),
        ("BlueIcon@3x.png", "iphone", "3x", "60x60"),
        ("BlueNotificationIcon.png", "ipad", "1x", "20x20"),
        ("BlueNotificationIcon@2x-1.png", "ipad", "2x", "20x20"),
        ("Simple@29x29.png", "ipad", "1x", "29x29"),
        ("Simple@58x58-1.png", "ipad", "2x", "29x29"),
        ("Simple@40x40-1.png", "ipad", "1x", "40x40"),
        ("Simple@80x80-1.png", "ipad", "2x", "40x40"),
        (None, "ipad", "1x", "76x76"),
        ("BlueIconIpad@2x.png", "ipad", "2x", "76x76"),
        ("BlueIconLargeIpad@2x.png", "ipad", "2x", "83.5x83.5"),
        ("Simple-iTunesArtwork.png", "ios-marketing", "1x", "1024x1024"),
    ]
    entries = []
    for filename, idiom, scale, size in images:
        e = {}
        if filename:
            e["filename"] = filename
        e["idiom"] = idiom
        e["scale"] = scale
        e["size"] = size
        entries.append(e)
    contents = {"images": entries, "info": {"author": "xcode", "version": 1}}
    with open(os.path.join(PNG_DIR, "Contents.json"), "w") as f:
        json.dump(contents, f, indent=2)
        f.write("\n")


def main():
    write_svg_layers()
    write_icon_json()
    write_png_set()
    print("Wrote", ICON_DIR)
    print("Wrote", PNG_DIR)


if __name__ == "__main__":
    main()
