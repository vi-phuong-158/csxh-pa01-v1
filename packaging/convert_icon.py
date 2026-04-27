import sys
import subprocess
from pathlib import Path

def install_pillow():
    try:
        import PIL
    except ImportError:
        print("Đang cài đặt thư viện Pillow để xử lý ảnh...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "Pillow"])

install_pillow()

from PIL import Image

def convert_png_to_ico(png_path, ico_path):
    img = Image.open(png_path)
    # Resize and save as ICO with multiple sizes to prevent blurring
    icon_sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    img.save(ico_path, format="ICO", sizes=icon_sizes)

if __name__ == "__main__":
    base_dir = Path(__file__).resolve().parent.parent
    png_file = base_dir / "assets" / "logo.png"
    ico_file = base_dir / "assets" / "logo.ico"
    
    if not png_file.exists():
        print(f"Không tìm thấy file: {png_file}")
        sys.exit(1)
        
    convert_png_to_ico(png_file, ico_file)
