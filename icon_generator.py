# icon_generator.py
import os
from PIL import Image, ImageDraw


def ensure_app_icon(icon_path: str = "app_icon.ico") -> str:
    """Generates a custom 256x256 cyber-blue shield & lightning bolt .ico file if not present."""
    if os.path.exists(icon_path):
        return icon_path

    try:
        size = 256
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Draw dark cyber-blue rounded background shield
        draw.rounded_rectangle(
            [(16, 16), (240, 240)],
            radius=52,
            fill=(22, 33, 52, 255),
            outline=(59, 142, 208, 255),
            width=10,
        )

        # Draw inner glowing accent ring
        draw.rounded_rectangle(
            [(32, 32), (224, 224)],
            radius=40,
            outline=(47, 165, 114, 180),
            width=4,
        )

        # Draw high-contrast gold/cyan lightning bolt in the center
        bolt_points = [
            (145, 42),
            (72, 138),
            (126, 138),
            (105, 214),
            (186, 114),
            (132, 114),
        ]
        draw.polygon(bolt_points, fill=(241, 196, 15, 255), outline=(255, 255, 255, 255))

        img.save(icon_path, format="ICO", sizes=[(256, 256), (64, 64), (32, 32), (16, 16)])
    except Exception:
        pass

    return icon_path


if __name__ == "__main__":
    path = ensure_app_icon()
    print(f"Generated custom icon at: {os.path.abspath(path)}")