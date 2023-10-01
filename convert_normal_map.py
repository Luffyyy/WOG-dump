from PIL import Image
import glob
import os
import sys

def convert_normal_map(path):
    for filename in glob.glob(f"{path}/*/*_n*.png"):
        img = Image.open(filename)
        img = img.convert("RGBA")
        r, g, b, a = img.split()
        img = Image.merge("RGB", (a, b, r))
        img.save(filename)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python convert_normal_map.py <path>")
        sys.exit(1)
    path = sys.argv[1]
    convert_normal_map(path)
