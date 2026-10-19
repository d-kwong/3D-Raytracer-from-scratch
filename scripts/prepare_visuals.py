#!/usr/bin/env python3
"""Reproduce the README cover and image comparisons (requires Pillow).

Run `make` first. This calls the maintained renderer, never historical scripts.
Use --reuse to compose images from already-rendered build/*.pgm files.
"""
import argparse
from pathlib import Path
import subprocess

from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parents[1]


def font(size):
    for name in ("DejaVuSans.ttf", "/System/Library/Fonts/Supplemental/Arial.ttf",
                 "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            pass
    return ImageFont.load_default()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reuse", action="store_true", help="reuse the existing intermediate PGMs")
    parser.add_argument("--threads", type=int, default=0, help="workers passed to the renderer (0=automatic)")
    args = parser.parse_args()
    output = ROOT / "docs/images"
    output.mkdir(parents=True, exist_ok=True)
    jobs = [("swirl-cover", 1600, 800, 80)] + [(f"swirl-grid{g}", 480, 240, g) for g in (8, 20, 80)]
    for name, width, height, grid in jobs:
        pgm = ROOT / "build" / f"{name}.pgm"
        if not args.reuse:
            subprocess.run([str(ROOT / "build/raytracer"), "--width", str(width), "--height", str(height),
                            "--grid", str(grid), "--threads", str(args.threads), "--output", str(pgm)],
                           cwd=ROOT, check=True)
        with Image.open(pgm) as image:
            if image.size != (width, height):
                raise ValueError(f"unexpected dimensions in {pgm.name}: {image.size}")
            if name == "swirl-cover":
                image.save(output / "swirl-cover.png")

    # These are actual renders at the same pixel resolution and camera settings.
    comparison = Image.new("RGB", (1480, 326), "#0d1117")
    draw = ImageDraw.Draw(comparison)
    draw.text((20, 12), "Same camera and 480 x 240 pixels; increasing the triangle mesh", font=font(22), fill="#e6edf3")
    for i, grid in enumerate((8, 20, 80)):
        x = 10 + i * 490
        with Image.open(ROOT / "build" / f"swirl-grid{grid}.pgm") as image:
            comparison.paste(image.convert("RGB"), (x, 48))
        draw.text((x + 10, 294), f"{grid} x {grid} cells / {2*grid*grid:,} triangles", font=font(19), fill="#b8c7da")
    comparison.save(output / "mesh-comparison.png")

    gallery = Image.new("RGB", (1480, 432), "#0d1117")
    draw = ImageDraw.Draw(gallery)
    draw.text((20, 12), "Original saved outputs / exact generation settings unverified", font=font(22), fill="#e6edf3")
    items = [("4_2000x1000.png", "Cosine hat / 2000 x 1000"),
             ("output.png", "Sphere-like output / 400 x 400"),
             ("swirl.png", "Swirl / 500 x 250")]
    for i, (name, label) in enumerate(items):
        x = 10 + i * 490
        with Image.open(ROOT / "experiments/images" / name) as image:
            # Preserve aspect ratio; do not infer or reconstruct missing details.
            fitted = ImageOps.contain(image.convert("RGB"), (480, 324), Image.Resampling.LANCZOS)
            gallery.paste(fitted, (x + (480-fitted.width)//2, 54 + (324-fitted.height)//2))
        draw.text((x + 8, 394), label, font=font(17), fill="#b8c7da")
    gallery.save(output / "original-gallery.png")
    print("Wrote cover, mesh comparison, and original artifact gallery to docs/images/")


if __name__ == "__main__":
    main()
