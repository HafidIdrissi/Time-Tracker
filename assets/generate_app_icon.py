"""Generate the Windows application icon from the editable SVG source."""

from io import BytesIO
from pathlib import Path
import subprocess

from PIL import Image

ASSETS = Path(__file__).resolve().parent
SVG = ASSETS / "app-icon.svg"
ICO = ASSETS / "app-icon.ico"
SIZES = (16, 32, 48, 64, 128, 256)


def main():
    rendered = {}

    for size in SIZES:
        result = subprocess.run(
            ["rsvg-convert", "-w", str(size), "-h", str(size), str(SVG)],
            check=True,
            capture_output=True,
        )
        with Image.open(BytesIO(result.stdout)) as image:
            rendered[size] = image.convert("RGBA")

    rendered[256].save(
        ICO,
        format="ICO",
        append_images=[rendered[size] for size in SIZES[:-1]],
        sizes=[(size, size) for size in SIZES],
    )

    with Image.open(ICO) as icon:
        actual_sizes = set(icon.ico.sizes())

    expected_sizes = {(size, size) for size in SIZES}
    if actual_sizes != expected_sizes:
        raise RuntimeError(f"Expected {expected_sizes}; found {actual_sizes}")

    print(f"Created: {ICO}")
    print(f"Verified sizes: {sorted(actual_sizes)}")


if __name__ == "__main__":
    main()
