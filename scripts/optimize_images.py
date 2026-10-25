#!/usr/bin/env python3
"""
scripts/optimize_images.py

Optimizes images in frontend/public and converts PNG/JPG to modern WebP format,
reporting before and after sizes.
"""
import os
import sys
from pathlib import Path
from PIL import Image

ROOT_DIR = Path(__file__).resolve().parent.parent
PUBLIC_DIR = ROOT_DIR / "frontend" / "public"


def optimize_image(image_path: Path):
    rel_path = image_path.relative_to(ROOT_DIR)
    initial_size = image_path.stat().st_size

    try:
        with Image.open(image_path) as img:
            # 1. Optimize PNG in-place if PNG
            if image_path.suffix.lower() == ".png":
                img.save(image_path, format="PNG", optimize=True)
                new_png_size = image_path.stat().st_size

                # 2. Generate modern WebP variant
                webp_path = image_path.with_suffix(".webp")
                img.save(webp_path, format="WEBP", quality=85, method=6)
                webp_size = webp_path.stat().st_size

                print(f"[OPTIMIZED] {rel_path}: {initial_size:,} bytes -> {new_png_size:,} bytes")
                print(f"[CREATED]   {webp_path.relative_to(ROOT_DIR)}: {webp_size:,} bytes ({((1 - webp_size / initial_size) * 100):.1f}% reduction)")

            elif image_path.suffix.lower() in [".jpg", ".jpeg"]:
                img.save(image_path, format="JPEG", optimize=True, quality=85)
                new_jpg_size = image_path.stat().st_size

                webp_path = image_path.with_suffix(".webp")
                img.save(webp_path, format="WEBP", quality=85, method=6)
                webp_size = webp_path.stat().st_size

                print(f"[OPTIMIZED] {rel_path}: {initial_size:,} bytes -> {new_jpg_size:,} bytes")
                print(f"[CREATED]   {webp_path.relative_to(ROOT_DIR)}: {webp_size:,} bytes")
    except Exception as e:
        print(f"[ERROR] Failed to optimize {image_path}: {e}", file=sys.stderr)


def main():
    if not PUBLIC_DIR.exists():
        print(f"Directory not found: {PUBLIC_DIR}")
        return

    print("Running image optimization for Carbon Horizon assets...")
    found = False
    for ext in ["*.png", "*.jpg", "*.jpeg"]:
        for file in PUBLIC_DIR.glob(ext):
            found = True
            optimize_image(file)

    if not found:
        print("No raster images found to optimize.")
    else:
        print("Image optimization complete.")


if __name__ == "__main__":
    main()
