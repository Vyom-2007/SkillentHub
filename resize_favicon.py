
import os
import sys

try:
    from PIL import Image
    print("Pillow is installed")
    
    img_path = 'app/static/favicon.png'
    if os.path.exists(img_path):
        img = Image.open(img_path)
        print(f"Original size: {img.size}")
        
        # Resize to 32x32
        img = img.resize((32, 32), Image.Resampling.LANCZOS)
        img.save(img_path)
        print(f"Resized to 32x32 and saved to {img_path}")
        
        # Also save as .ico
        icon_path = 'app/static/favicon.ico'
        img.save(icon_path, format='ICO')
        print(f"Saved favicon.ico to {icon_path}")
        
    else:
        print(f"File not found: {img_path}")

except ImportError:
    print("Pillow not installed")
except Exception as e:
    print(f"Error: {e}")
