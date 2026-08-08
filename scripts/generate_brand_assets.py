"""Generate deterministic raster assets from the InsightForge brand mark."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
PURPLE = "#7057F5"
PURPLE_DARK = "#5A42DD"
WHITE = "#FFFFFF"


def _sparkle(draw: ImageDraw.ImageDraw, center: tuple[int, int], radius: int) -> None:
    x, y = center
    points = [
        (x, y - radius),
        (x + radius // 3, y - radius // 3),
        (x + radius, y),
        (x + radius // 3, y + radius // 3),
        (x, y + radius),
        (x - radius // 3, y + radius // 3),
        (x - radius, y),
        (x - radius // 3, y - radius // 3),
    ]
    draw.polygon(points, fill=WHITE)


def generate() -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)
    size = 1024
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((56, 56, 968, 968), radius=250, fill=PURPLE)
    draw.rounded_rectangle((92, 92, 932, 932), radius=220, outline=PURPLE_DARK, width=18)
    _sparkle(draw, (460, 500), 190)
    _sparkle(draw, (700, 310), 92)
    _sparkle(draw, (720, 675), 62)

    resampling = Image.Resampling.LANCZOS
    icon_png = image.resize((512, 512), resampling)
    icon_png.save(ASSETS / "icon.png", optimize=True)
    image.save(
        ASSETS / "icon.ico",
        sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
    )


if __name__ == "__main__":
    generate()

