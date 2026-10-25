from PIL import Image, ImageDraw, ImageFont
import math
import os

width = 1200
height = 630

# Create base image
img = Image.new("RGBA", (width, height), (7, 12, 20, 255))
draw = ImageDraw.Draw(img)

# 1. Radial/Vertical gradient background
for y in range(height):
    ratio = y / height
    # Deep slate-emerald gradient
    r = int(14 * (1 - ratio) + 4 * ratio)
    g = int(42 * (1 - ratio) + 12 * ratio)
    b = int(34 * (1 - ratio) + 18 * ratio)
    draw.line([(0, y), (width, y)], fill=(r, g, b, 255))

# 2. Ambient Horizon Glow
glow_center_x, glow_center_y = 600, 220
max_radius = 280
for r in range(max_radius, 0, -5):
    alpha = int(45 * (1 - r / max_radius))
    bbox = [glow_center_x - r, glow_center_y - r, glow_center_x + r, glow_center_y + r]
    draw.ellipse(bbox, fill=(16, 185, 129, alpha))

# Secondary glows
for r in range(160, 0, -5):
    alpha = int(30 * (1 - r / 160))
    bbox = [240 - r, 360 - r, 240 + r, 360 + r]
    draw.ellipse(bbox, fill=(2, 132, 199, alpha))

# 3. Horizon landscape curve
points1 = []
for x in range(-50, width + 50, 10):
    y = int(500 + 40 * math.sin((x + 200) / 250))
    points1.append((x, y))
points1.append((width + 50, height + 50))
points1.append((-50, height + 50))
draw.polygon(points1, fill=(4, 18, 26, 230))

# Glowing horizon line
for i in range(len(points1) - 3):
    x1, y1 = points1[i]
    x2, y2 = points1[i+1]
    draw.line([(x1, y1), (x2, y2)], fill=(110, 231, 183, 200), width=3)
    draw.line([(x1, y1 - 1), (x2, y2 - 1)], fill=(52, 211, 153, 100), width=2)

# 4. Central Glass Card
card_x1, card_y1, card_x2, card_y2 = 140, 75, 1060, 545
card_radius = 28
# Draw card shadow
draw.rounded_rectangle([card_x1 - 4, card_y1 - 4, card_x2 + 4, card_y2 + 4], radius=card_radius + 4, fill=(0, 0, 0, 60))
# Draw card fill
draw.rounded_rectangle([card_x1, card_y1, card_x2, card_y2], radius=card_radius, fill=(11, 23, 36, 210), outline=(52, 211, 153, 120), width=2)

# 5. Logo icon
logo_cx, logo_cy = 600, 165
draw.ellipse([logo_cx - 44, logo_cy - 44, logo_cx + 44, logo_cy + 44], fill=(16, 185, 129, 40), outline=(110, 231, 183, 200), width=2)
draw.ellipse([logo_cx - 34, logo_cy - 34, logo_cx + 34, logo_cy + 34], fill=(9, 32, 25, 255))
# Leaf shape
draw.chord([logo_cx - 18, logo_cy - 20, logo_cx + 18, logo_cy + 16], start=45, end=225, fill=(52, 211, 153, 255))
draw.arc([logo_cx - 28, logo_cy - 5, logo_cx + 28, logo_cy + 18], start=190, end=350, fill=(56, 189, 248, 255), width=3)

# 6. Typography
# Try system fonts
font_large = None
font_sub = None
font_pill = None

font_candidates = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
]
for fc in font_candidates:
    if os.path.exists(fc):
        try:
            font_large = ImageFont.truetype(fc, 52)
            font_sub = ImageFont.truetype(fc.replace("Bold", ""), 22)
            font_pill = ImageFont.truetype(fc, 15)
            break
        except Exception:
            pass

if not font_large:
    font_large = ImageFont.load_default()
    font_sub = ImageFont.load_default()
    font_pill = ImageFont.load_default()

# Title: Carbon Horizon
title_text = "Carbon Horizon"
draw.text((600, 275), title_text, fill=(255, 255, 255, 255), font=font_large, anchor="mm")

# Subtitle
sub_text = "Personal Climate Intelligence & AI Sustainability Coach"
draw.text((600, 335), sub_text, fill=(148, 163, 184, 255), font=font_sub, anchor="mm")

# 7. Feature Pills
pills = [
    ("Track Footprint", (52, 211, 153), -220),
    ("Simulate Reductions", (56, 189, 248), 0),
    ("AI Climate Coach", (167, 139, 250), 220),
]

for label, color, offset_x in pills:
    px = 600 + offset_x
    py = 415
    pw, ph = 190, 36
    draw.rounded_rectangle([px - pw // 2, py - ph // 2, px + pw // 2, py + ph // 2], radius=18, fill=(30, 41, 59, 220), outline=(51, 65, 85, 255), width=1)
    draw.ellipse([px - pw // 2 + 14, py - 4, px - pw // 2 + 22, py + 4], fill=color)
    draw.text((px + 8, py), label, fill=(226, 232, 240, 255), font=font_pill, anchor="mm")

# 8. Bottom branding
draw.text((600, 495), "CARBONHORIZON.APP", fill=(71, 85, 105, 255), font=font_pill, anchor="mm")

# Save optimized PNG
output_path = "frontend/public/og-image.png"
rgb_img = img.convert("RGB")
rgb_img.save(output_path, "PNG", optimize=True)

size_kb = os.path.getsize(output_path) / 1024
print(f"Generated {output_path}: {size_kb:.1f} KB")
