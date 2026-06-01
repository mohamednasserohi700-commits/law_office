from PIL import Image


def main():
    im = Image.open("static/img/brand-logo.png").convert("RGBA")
    w, h = im.size
    px = im.load()
    pts = [
        (0, 0),
        (w - 1, 0),
        (0, h - 1),
        (w - 1, h - 1),
        (w // 2, 0),
        (w // 2, h - 1),
        (0, h // 2),
        (w - 1, h // 2),
    ]
    print("size", (w, h))
    for p in pts:
        print(p, "alpha", px[p][3])


if __name__ == "__main__":
    main()

