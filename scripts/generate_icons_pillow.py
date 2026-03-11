from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import math
import shutil

ROOT = Path(__file__).resolve().parents[1] / "static" / "images"
ROOT.mkdir(parents=True, exist_ok=True)

COLORS = {
    "bg_dark_1": (0x0D, 0x11, 0x17),
    "bg_dark_2": (0x08, 0x0C, 0x10),
    "gold_1": (0xF0, 0xC0, 0x60),
    "gold_2": (0xC9, 0xA8, 0x4C),
    "green_1": (0x1A, 0x6B, 0x4A),
    "green_2": (0x0D, 0x4A, 0x33),
    "purple_1": (0x1A, 0x0D, 0x2E),
}

FONT_PATHS = [
    r"C:\Windows\Fonts\arialbd.ttf",
    r"C:\Windows\Fonts\arial.ttf",
    r"C:\Windows\Fonts\segoeui.ttf",
    r"C:\Windows\Fonts\seguisb.ttf",
    r"C:\Windows\Fonts\georgia.ttf",
    r"C:\Windows\Fonts\times.ttf",
]

def load_font(size, prefer_serif=False):
    paths = FONT_PATHS[:]
    if prefer_serif:
        paths = [p for p in paths if "georgia" in p.lower() or "times" in p.lower()] + paths
    for path in paths:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            continue
    return ImageFont.load_default()


def lerp(a, b, t):
    return int(a + (b - a) * t)


def linear_gradient(size, c1, c2, horizontal=False):
    w, h = size
    base = Image.new("RGBA", (w, h))
    pix = base.load()
    for y in range(h):
        for x in range(w):
            t = x / (w - 1) if horizontal else y / (h - 1)
            r = lerp(c1[0], c2[0], t)
            g = lerp(c1[1], c2[1], t)
            b = lerp(c1[2], c2[2], t)
            pix[x, y] = (r, g, b, 255)
    return base


def radial_glow(size, center, radius, color):
    w, h = size
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    pix = img.load()
    cx, cy = center
    for y in range(h):
        for x in range(w):
            dx = x - cx
            dy = y - cy
            d = math.sqrt(dx * dx + dy * dy)
            if d <= radius:
                t = 1 - (d / radius)
                a = int(255 * t * 0.3)
                pix[x, y] = (color[0], color[1], color[2], a)
    return img


def rounded_mask(size, radius):
    mask = Image.new("L", size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle([0, 0, size[0], size[1]], radius=radius, fill=255)
    return mask


def paste_gradient_shape(base, gradient, mask):
    temp = Image.new("RGBA", base.size, (0, 0, 0, 0))
    temp.paste(gradient.resize(base.size), (0, 0))
    base.alpha_composite(temp, (0, 0), mask)


def draw_star(draw, points, fill):
    draw.polygon(points, fill=fill)


def icon_ios():
    size = (180, 180)
    bg = linear_gradient(size, COLORS["bg_dark_1"], COLORS["bg_dark_2"], horizontal=True)
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    img.paste(bg, (0, 0), rounded_mask(size, 40))
    draw = ImageDraw.Draw(img)

    gold = linear_gradient(size, COLORS["gold_1"], COLORS["gold_2"], horizontal=True)

    crescent_mask = Image.new("L", size, 0)
    cm = ImageDraw.Draw(crescent_mask)
    cm.ellipse([90 - 45, 80 - 45, 90 + 45, 80 + 45], fill=255)
    img.paste(gold, (0, 0), crescent_mask)

    draw.ellipse([110 - 38, 68 - 38, 110 + 38, 68 + 38], fill=COLORS["bg_dark_1"])

    star_pts = [
        (90, 65), (94, 82), (108, 75), (101, 89), (118, 93),
        (101, 97), (108, 111), (94, 104), (90, 121), (86, 104),
        (72, 111), (79, 97), (62, 93), (79, 89), (72, 75), (86, 82),
    ]
    star_mask = Image.new("L", size, 0)
    sm = ImageDraw.Draw(star_mask)
    sm.polygon(star_pts, fill=255)
    img.paste(gold, (0, 0), star_mask)

    font = load_font(22)
    text = "???"
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    draw.text(((size[0] - tw) / 2, 155 - th / 2), text, font=font, fill=COLORS["gold_2"])

    img.save(ROOT / "icon-ios.png", optimize=True)


def icon_android():
    size = (192, 192)
    bg = linear_gradient(size, COLORS["green_1"], COLORS["green_2"], horizontal=True)
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    img.paste(bg, (0, 0), rounded_mask(size, 48))

    gold = linear_gradient(size, COLORS["gold_1"], COLORS["gold_2"], horizontal=True)

    mask = Image.new("L", size, 0)
    d = ImageDraw.Draw(mask)
    d.ellipse([96 - 40, 85 - 35, 96 + 40, 85 + 35], fill=255)
    d.rectangle([56, 85, 136, 140], fill=255)
    d.rectangle([42, 65, 56, 140], fill=255)
    d.ellipse([49 - 7, 65 - 10, 49 + 7, 65 + 10], fill=255)
    d.rectangle([136, 65, 150, 140], fill=255)
    d.ellipse([143 - 7, 65 - 10, 143 + 7, 65 + 10], fill=255)
    img.paste(gold, (0, 0), mask)

    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([82, 105, 110, 140], radius=14, fill=COLORS["green_2"])

    crescent_mask = Image.new("L", size, 0)
    cm = ImageDraw.Draw(crescent_mask)
    cm.ellipse([96 - 10, 52 - 10, 96 + 10, 52 + 10], fill=255)
    img.paste(gold, (0, 0), crescent_mask)
    draw.ellipse([102 - 8, 48 - 8, 102 + 8, 48 + 8], fill=COLORS["green_1"])

    font = load_font(16)
    text = "NurCoran"
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    draw.text(((size[0] - tw) / 2, 175 - th / 2), text, font=font, fill=COLORS["gold_1"])

    img.save(ROOT / "icon-android.png", optimize=True)


def quad_points(p0, p1, p2, steps=20):
    pts = []
    for i in range(steps + 1):
        t = i / steps
        x = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t ** 2 * p2[0]
        y = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t ** 2 * p2[1]
        pts.append((x, y))
    return pts


def icon_desktop():
    size = (512, 512)
    bg = linear_gradient(size, COLORS["bg_dark_1"], COLORS["bg_dark_2"], horizontal=True)
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    img.paste(bg, (0, 0), rounded_mask(size, 80))

    glow = radial_glow(size, (256, 240), 180, COLORS["gold_2"])
    img.alpha_composite(glow)

    draw = ImageDraw.Draw(img)
    ray_color = (COLORS["gold_2"][0], COLORS["gold_2"][1], COLORS["gold_2"][2], int(255 * 0.4))
    draw.line([256, 80, 256, 130], fill=ray_color, width=3)
    draw.line([350, 110, 320, 148], fill=ray_color, width=3)
    draw.line([162, 110, 192, 148], fill=ray_color, width=3)
    draw.line([390, 200, 345, 210], fill=ray_color, width=3)
    draw.line([122, 200, 167, 210], fill=ray_color, width=3)

    gold = linear_gradient(size, COLORS["gold_1"], COLORS["gold_2"], horizontal=True)

    left = []
    left += quad_points((130, 180), (256, 160), (256, 300), steps=24)
    left += quad_points((256, 300), (200, 310), (130, 300), steps=24)
    mask = Image.new("L", size, 0)
    ImageDraw.Draw(mask).polygon(left, fill=255)
    img.paste(gold, (0, 0), mask)

    right = []
    right += quad_points((382, 180), (256, 160), (256, 300), steps=24)
    right += quad_points((256, 300), (312, 310), (382, 300), steps=24)
    mask = Image.new("L", size, 0)
    ImageDraw.Draw(mask).polygon(right, fill=255)
    img.paste(gold, (0, 0), mask)

    draw.rounded_rectangle([250, 160, 262, 305], radius=6, fill=COLORS["gold_2"])

    line_color = (COLORS["bg_dark_2"][0], COLORS["bg_dark_2"][1], COLORS["bg_dark_2"][2], int(255 * 0.5))
    draw.line([160, 210, 240, 205], fill=line_color, width=3)
    draw.line([155, 225, 238, 220], fill=line_color, width=3)
    draw.line([152, 240, 237, 235], fill=line_color, width=3)
    draw.line([150, 255, 236, 250], fill=line_color, width=3)

    draw.line([272, 205, 352, 210], fill=line_color, width=3)
    draw.line([274, 220, 357, 225], fill=line_color, width=3)
    draw.line([275, 235, 360, 240], fill=line_color, width=3)
    draw.line([276, 250, 362, 255], fill=line_color, width=3)

    crescent_mask = Image.new("L", size, 0)
    cm = ImageDraw.Draw(crescent_mask)
    cm.ellipse([256 - 22, 148 - 22, 256 + 22, 148 + 22], fill=255)
    img.paste(gold, (0, 0), crescent_mask)
    draw.ellipse([267 - 17, 140 - 17, 267 + 17, 140 + 17], fill=COLORS["bg_dark_1"])
    draw.ellipse([256 - 5, 128 - 5, 256 + 5, 128 + 5], fill=COLORS["gold_2"])

    font_main = load_font(48, prefer_serif=True)
    text = "NurCoran"
    bbox = draw.textbbox((0, 0), text, font=font_main)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    draw.text(((size[0] - tw) / 2, 360 - th / 2), text, font=font_main, fill=COLORS["gold_2"])

    font_sub = load_font(24)
    text2 = "??? ??????"
    bbox = draw.textbbox((0, 0), text2, font=font_sub)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    draw.text(((size[0] - tw) / 2, 400 - th / 2), text2, font=font_sub, fill=(COLORS["gold_2"][0], COLORS["gold_2"][1], COLORS["gold_2"][2], int(255 * 0.7)))

    img.save(ROOT / "icon-desktop.png", optimize=True)


def icon_ipad():
    size = (167, 167)
    bg = linear_gradient(size, COLORS["purple_1"], COLORS["bg_dark_2"], horizontal=True)
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    img.paste(bg, (0, 0), rounded_mask(size, 35))

    gold = linear_gradient(size, COLORS["gold_1"], COLORS["gold_2"], horizontal=True)

    star_pts = [
        (83, 25), (91, 55), (118, 38), (101, 62), (131, 70),
        (101, 78), (118, 102), (91, 85), (83, 115), (75, 85),
        (48, 102), (65, 78), (35, 70), (65, 62), (48, 38), (75, 55),
    ]
    mask = Image.new("L", size, 0)
    ImageDraw.Draw(mask).polygon(star_pts, fill=255)
    img.paste(gold, (0, 0), mask)

    draw = ImageDraw.Draw(img)
    draw.ellipse([83 - 22, 70 - 22, 83 + 22, 70 + 22], fill=COLORS["purple_1"])

    crescent_mask = Image.new("L", size, 0)
    cm = ImageDraw.Draw(crescent_mask)
    cm.ellipse([83 - 16, 70 - 16, 83 + 16, 70 + 16], fill=255)
    img.paste(gold, (0, 0), crescent_mask)
    draw.ellipse([90 - 13, 65 - 13, 90 + 13, 65 + 13], fill=COLORS["purple_1"])
    draw.ellipse([83 - 4, 70 - 4, 83 + 4, 70 + 4], fill=COLORS["gold_2"])

    font = load_font(15)
    text = "NurCoran"
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    draw.text(((size[0] - tw) / 2, 138 - th / 2), text, font=font, fill=COLORS["gold_2"])

    font2 = load_font(11)
    text2 = "??? ??????"
    bbox = draw.textbbox((0, 0), text2, font=font2)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    draw.text(((size[0] - tw) / 2, 156 - th / 2), text2, font=font2, fill=(COLORS["gold_2"][0], COLORS["gold_2"][1], COLORS["gold_2"][2], int(255 * 0.6)))

    img.save(ROOT / "icon-ipad.png", optimize=True)


if __name__ == "__main__":
    icon_ios()
    icon_android()
    icon_desktop()
    icon_ipad()

    shutil.copy(ROOT / "icon-ios.png", ROOT / "icon-192.png")
    shutil.copy(ROOT / "icon-desktop.png", ROOT / "icon-512.png")

    print("Toutes les icones creees")
