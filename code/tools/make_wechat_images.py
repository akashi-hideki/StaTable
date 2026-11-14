"""Generate 3 images for WeChat posting (StaTable v3.4.3).

Images:
  1. cover.png        1200x630  Title + badges + key numbers
  2. architecture.png 1200x800  7-layer architecture diagram
  3. features.png     1200x630  Features + download info

Usage:
  python code/tools/make_wechat_images.py

Requires: Pillow  (pip install Pillow)
"""
from __future__ import annotations

import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("ERROR: Pillow is required. Run: pip install Pillow")
    sys.exit(2)


SCRIPT = Path(__file__).resolve()
REPO = SCRIPT.parent.parent.parent
OUT = REPO / "wechat_images"

# ---------- Colors ----------
BG = (13, 27, 42)
PANEL = (27, 38, 59)
PANEL2 = (35, 48, 71)
FG = (235, 240, 245)
SUB = (160, 175, 190)
ACCENT = (0, 200, 255)
ACCENT2 = (255, 183, 3)
GREEN = (80, 220, 130)

FONT_CANDIDATES = [
    r"C:\Windows\Fonts\msyhbd.ttc",
    r"C:\Windows\Fonts\msyh.ttc",
    r"C:\Windows\Fonts\simhei.ttf",
    r"C:\Windows\Fonts\segoeui.ttf",
]
FONT_CACHE = {}


def font(size):
    if size in FONT_CACHE:
        return FONT_CACHE[size]
    for p in FONT_CANDIDATES:
        if Path(p).exists():
            f = ImageFont.truetype(p, size)
            FONT_CACHE[size] = f
            return f
    FONT_CACHE[size] = ImageFont.load_default()
    return FONT_CACHE[size]


def text_w(d, s, f):
    bbox = d.textbbox((0, 0), s, font=f)
    return bbox[2] - bbox[0]


def rounded(d, x, y, w, h, fill, outline=None, radius=14, width=2):
    d.rounded_rectangle((x, y, x + w, y + h),
                        radius=radius, fill=fill,
                        outline=outline, width=width)


# ==================================================
# Image 1: cover.png (1200 x 630)
# ==================================================
def make_cover():
    W, H = 1200, 630
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    d.rectangle((0, 0, W, 6), fill=ACCENT)

    d.text((60, 50), "StaTable v3.4.3", font=font(40), fill=FG)
    d.text((60, 100), "2026-10-10  Release", font=font(22), fill=SUB)

    d.text((60, 200), "七层架构状态机", font=font(72), fill=FG)
    d.text((60, 290), "C 代码生成器", font=font(72), fill=ACCENT)

    d.text((60, 400),
           "MISRA C:2012 合规 · 嵌入式 C99 · Cortex-M4",
           font=font(26), fill=SUB)

    badges = [
        ("7 层", ACCENT),
        ("31 状态", ACCENT),
        ("60 Role", ACCENT2),
        ("45 测试套件", GREEN),
    ]
    x = 60
    for label, color in badges:
        w = text_w(d, label, font(24)) + 40
        rounded(d, x, 500, w, 56, PANEL2, outline=color, radius=28)
        d.text((x + 20, 514), label, font=font(24), fill=color)
        x += w + 20

    d.text((60, 590),
           "github.com/akashi-hideki/StaTable",
           font=font(20), fill=SUB)

    img.save(OUT / "cover.png", "PNG")
    print(f"[OK] {OUT / 'cover.png'}")


# ==================================================
# Image 2: architecture.png (1200 x 800)
# ==================================================
def make_architecture():
    W, H = 1200, 800
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    d.rectangle((0, 0, W, 6), fill=ACCENT)
    d.text((60, 40), "七层架构", font=font(44), fill=FG)
    d.text((60, 100), "7-Layer Architecture  /  StaTable v3.4.3",
           font=font(22), fill=SUB)

    # Panel (Android)
    px, py, pw, ph = 360, 160, 480, 60
    rounded(d, px, py, pw, ph, PANEL2, outline=ACCENT, radius=12)
    d.text((px + pw / 2 - text_w(d, "Android 面板 (主控)", font(24)) / 2,
            py + 16), "Android 面板 (主控)", font=font(24), fill=ACCENT)

    # Arrow
    d.line((600, py + ph, 600, py + ph + 40), fill=SUB, width=2)
    d.polygon([(600, py + ph + 46),
               (595, py + ph + 38),
               (605, py + ph + 38)], fill=SUB)
    d.text((620, py + ph + 8), "AC 零交叉同步串行",
           font=font(18), fill=SUB)

    # App layer
    ax, ay, aw, ah = 360, 290, 480, 60
    rounded(d, ax, ay, aw, ah, PANEL, outline=GREEN, radius=12)
    d.text((ax + aw / 2 - text_w(d, "Application  (5 状态)", font(24)) / 2,
            ay + 16), "Application  (5 状态)",
           font=font(24), fill=GREEN)

    # 4 sub-boxes
    subs = [
        ("MwMicrowave", "4 状态"),
        ("MwOven", "3 状态"),
        ("MwGrill", "3 状态"),
        ("MwSteam", "5 状态"),
    ]
    sub_w = 260
    sub_h = 80
    sub_y = 420
    gap = (1080 - 60 - 4 * sub_w) / 3 + 20
    xs = [60, 60 + sub_w + gap, 60 + 2 * (sub_w + gap),
          60 + 3 * (sub_w + gap)]

    for (nm, st), x in zip(subs, xs):
        rounded(d, x, sub_y, sub_w, sub_h, PANEL, outline=ACCENT2, radius=12)
        d.text((x + sub_w / 2 - text_w(d, nm, font(24)) / 2, sub_y + 14),
               nm, font=font(24), fill=ACCENT2)
        d.text((x + sub_w / 2 - text_w(d, st, font(18)) / 2, sub_y + 48),
               st, font=font(18), fill=SUB)
        # arrow from App
        d.line((ax + aw / 2, ay + ah, x + sub_w / 2, sub_y),
               fill=SUB, width=1)

    # DriverInput / DriverOutput
    di_x, di_y, di_w, di_h = 60, 580, 510, 80
    do_x, do_y, do_w, do_h = 630, 580, 510, 80
    rounded(d, di_x, di_y, di_w, di_h, PANEL2, outline=ACCENT, radius=12)
    d.text((di_x + 20, di_y + 12), "DriverInput",
           font=font(26), fill=ACCENT)
    d.text((di_x + 20, di_y + 48), "5 状态  ·  传感器 / RX / 门",
           font=font(18), fill=SUB)

    rounded(d, do_x, do_y, do_w, do_h, PANEL2, outline=ACCENT, radius=12)
    d.text((do_x + 20, do_y + 12), "DriverOutput",
           font=font(26), fill=ACCENT)
    d.text((do_x + 20, do_y + 48), "6 状态  ·  加热器 / 风扇 / TX",
           font=font(18), fill=SUB)

    # arrows from sub to driver
    for x in xs:
        d.line((x + sub_w / 2, sub_y + sub_h, x + sub_w / 2, di_y),
               fill=SUB, width=1)

    # Footer
    d.text((60, 720),
           "31 states  ·  60 roles  ·  74 transitions",
           font=font(22), fill=SUB)

    img.save(OUT / "architecture.png", "PNG")
    print(f"[OK] {OUT / 'architecture.png'}")


# ==================================================
# Image 3: features.png (1200 x 630)
# ==================================================
def make_features():
    W, H = 1200, 630
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    d.rectangle((0, 0, W, 6), fill=ACCENT2)
    d.text((60, 40), "StaTable v3.4.3  核心特性",
           font=font(44), fill=FG)

    features = [
        ("7 层架构", "Application / 4 中间层 / DriverInput + DriverOutput"),
        ("表驱动 C99 生成", "状态 × 事件矩阵 → 可读 C 代码"),
        ("MISRA C:2012", "cppcheck 检测 · 10 hits 抑制（设计上）"),
        ("UML 状态动作", "Entry / Exit / Do 完整支持 + 用户代码保护"),
        ("3 语言文档", "中文 / English / 日本語（含全 SPEC）"),
        ("测试验证", "gcc 27/27 PASS · arm 27/27 PASS · LINK PASS"),
    ]

    y = 130
    for title, desc in features:
        # check mark
        d.text((60, y), "✓", font=font(30), fill=GREEN)
        d.text((110, y), title, font=font(28), fill=FG)
        d.text((110, y + 38), desc, font=font(20), fill=SUB)
        y += 78

    # Download panel
    px, py, pw, ph = 60, 480, 1080, 120
    rounded(d, px, py, pw, ph, PANEL, outline=ACCENT, radius=14)
    d.text((px + 30, py + 16), "下载 / Download",
           font=font(24), fill=ACCENT)
    d.text((px + 30, py + 52),
           "GitHub: github.com/akashi-hideki/StaTable/releases/tag/v3.4.3",
           font=font(18), fill=FG)
    d.text((px + 30, py + 82),
           "PyPI: pip install statable==3.4.3",
           font=font(18), fill=FG)

    img.save(OUT / "features.png", "PNG")
    print(f"[OK] {OUT / 'features.png'}")


# ==================================================
# Main
# ==================================================
def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    print(f"[i] Output dir: {OUT}\n")

    make_cover()
    make_architecture()
    make_features()

    print(f"\n[PASS] 3 images generated in {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())