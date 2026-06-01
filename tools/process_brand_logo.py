import argparse
from collections import deque
from pathlib import Path

from PIL import Image, ImageEnhance, ImageFilter


def _color_dist(a, b) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1]) + abs(a[2] - b[2])


def _is_bg(rgb, bg_samples, threshold: int) -> bool:
    return any(_color_dist(rgb, s) <= threshold for s in bg_samples)


def remove_checkerboard_background(im: Image.Image, threshold: int = 36) -> Image.Image:
    """
    Remove a flat/near-flat background that's connected to image borders.
    Designed for exported logos that accidentally include a checkerboard "transparency" layer.
    """
    rgba = im.convert("RGBA")
    w, h = rgba.size
    px = rgba.load()

    # Sample likely background colors from corners + a few edge points.
    sample_points = [
        (0, 0),
        (w - 1, 0),
        (0, h - 1),
        (w - 1, h - 1),
        (w // 2, 0),
        (w // 2, h - 1),
        (0, h // 2),
        (w - 1, h // 2),
    ]
    bg_samples = []
    for x, y in sample_points:
        r, g, b, a = px[x, y]
        if a > 0:
            bg_samples.append((r, g, b))
    if not bg_samples:
        return rgba

    # Flood fill from borders for pixels that look like background.
    q = deque()
    seen = [[False] * w for _ in range(h)]
    bg = [[False] * w for _ in range(h)]

    def push(x, y):
        if 0 <= x < w and 0 <= y < h and not seen[y][x]:
            seen[y][x] = True
            q.append((x, y))

    for x in range(w):
        push(x, 0)
        push(x, h - 1)
    for y in range(h):
        push(0, y)
        push(w - 1, y)

    while q:
        x, y = q.popleft()
        r, g, b, a = px[x, y]
        if a == 0:
            bg[y][x] = True
        else:
            if _is_bg((r, g, b), bg_samples, threshold):
                bg[y][x] = True
            else:
                continue
        push(x + 1, y)
        push(x - 1, y)
        push(x, y + 1)
        push(x, y - 1)

    # Also remove background-looking pixels anywhere (e.g. inner checkerboard inside rings).
    def looks_like_checkerboard(rgb) -> bool:
        r, g, b = rgb
        mx = max(r, g, b)
        mn = min(r, g, b)
        # near-neutral light gray/white tiles
        if mx < 205:
            return False
        if (mx - mn) > 14:
            return False
        return _is_bg((r, g, b), bg_samples, threshold)

    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a and looks_like_checkerboard((r, g, b)):
                bg[y][x] = True

    # Build an alpha mask (foreground=255, background=0) then soften edges slightly.
    mask = Image.new("L", (w, h), 255)
    mpx = mask.load()
    for y in range(h):
        row_bg = bg[y]
        for x in range(w):
            if row_bg[x]:
                mpx[x, y] = 0

    # Feather edges for clean anti-aliased cutout.
    mask = mask.filter(ImageFilter.GaussianBlur(radius=1.25))
    # Clamp very low alpha to fully transparent to avoid speckle.
    mask = mask.point(lambda v: 0 if v < 10 else v)

    out = rgba.copy()
    out.putalpha(mask)
    return out


def enhance_premium_gold(im: Image.Image) -> Image.Image:
    # Subtle global enhancements: slightly higher contrast, micro-sharpening.
    out = im
    out = ImageEnhance.Contrast(out).enhance(1.08)
    out = ImageEnhance.Color(out).enhance(1.05)
    out = out.filter(ImageFilter.UnsharpMask(radius=1.6, percent=135, threshold=2))
    return out


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--in", dest="inp", required=True, help="Input logo path (png/jpg)")
    p.add_argument("--out", dest="out", required=True, help="Output transparent png path")
    p.add_argument("--threshold", type=int, default=36, help="Background similarity threshold")
    p.add_argument("--pad", type=int, default=60, help="Padding around emblem in output canvas")
    args = p.parse_args()

    inp = Path(args.inp)
    outp = Path(args.out)
    outp.parent.mkdir(parents=True, exist_ok=True)

    im = Image.open(inp)
    cut = remove_checkerboard_background(im, threshold=args.threshold)

    # Trim empty edges then add padding.
    bbox = cut.getbbox()
    if bbox:
        cut = cut.crop(bbox)
    w, h = cut.size
    padded = Image.new("RGBA", (w + args.pad * 2, h + args.pad * 2), (0, 0, 0, 0))
    padded.paste(cut, (args.pad, args.pad), cut)

    enhanced = enhance_premium_gold(padded)
    enhanced.save(outp, format="PNG", optimize=True)


if __name__ == "__main__":
    main()

