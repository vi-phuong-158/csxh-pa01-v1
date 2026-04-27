from pathlib import Path

try:
    from PIL import Image
except ImportError:
    import subprocess, sys
    print("[!] Pillow not found. Installing...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "Pillow"])
    from PIL import Image

ROOT = Path(__file__).parent.parent.resolve()
SRC  = ROOT / "assets" / "logo.png"
DEST = ROOT / "assets" / "logo.ico"
ICO_SIZES = [(16,16), (24,24), (32,32), (48,48), (64,64), (128,128), (256,256)]

def convert():
    if not SRC.exists():
        print(f"[x] Not found: {SRC}")
        print("    Please put logo.png in assets/ folder")
        return

    print(f"[>] Converting: {SRC.name} -> {DEST.name}")
    img = Image.open(SRC).convert("RGBA")

    images = []
    for size in ICO_SIZES:
        resized = img.resize(size, Image.LANCZOS)
        images.append(resized)

    images[0].save(
        DEST,
        format="ICO",
        sizes=ICO_SIZES,
        append_images=images[1:]
    )
    print(f"[v] Created: {DEST}")
    print(f"    Sizes: {[f'{s[0]}x{s[1]}' for s in ICO_SIZES]}")

if __name__ == "__main__":
    convert()
