import argparse
import json
import pickle
import sys
from typing import Dict, Tuple

from PIL import Image

PALETTE = {
    (0, 0, 0): 0,
    (255, 255, 255): 1,
    (170, 170, 170): 2,
    (85, 85, 85): 3,
    (254, 211, 199): 4,
    (255, 196, 206): 5,
    (250, 172, 142): 6,
    (255, 139, 131): 7,
    (244, 67, 54): 8,
    (233, 30, 99): 9,
    (226, 102, 158): 10,
    (156, 39, 176): 11,
    (103, 58, 183): 12,
    (63, 81, 181): 13,
    (0, 70, 112): 14,
    (5, 113, 151): 15,
    (33, 150, 243): 16,
    (0, 188, 212): 17,
    (59, 229, 219): 18,
    (151, 253, 220): 19,
    (22, 115, 0): 20,
    (55, 169, 60): 21,
    (137, 230, 66): 22,
    (215, 255, 7): 23,
    (255, 246, 209): 24,
    (248, 203, 140): 25,
    (255, 235, 59): 26,
    (255, 193, 7): 27,
    (255, 152, 0): 28,
    (255, 87, 34): 29,
    (184, 63, 39): 30,
    (121, 85, 72): 31,
}

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", "-i", default="./src.jpg")
    parser.add_argument("--output-pic", "-op", default="./out.png")
    parser.add_argument("--dest", "-d", default="output")
    parser.add_argument("--fast", "-f", action="store_true")
    parser.add_argument("--left", "-l", type=int, default=0)
    parser.add_argument("--up", "-u", type=int, default=0)

    namespace = parser.parse_args()

    input_dest: str = namespace.input
    output_pic_dest: str = namespace.output_pic
    dest: str = namespace.dest
    fast: bool = namespace.fast
    left: int = namespace.left
    up: int = namespace.up

    palette_image = Image.new("P", (16, 16))

    palettedata = []

    for (k, v) in PALETTE.items():
        for i in range(3):
            palettedata += [k[i]]
    palettedata += [0] * 3 * (256 - 32)

    palette_image.putpalette(palettedata)

    src_img = Image.open(input_dest).convert("RGB")

    src_img.load()
    palette_image.load()

    dst_img: Image.Image = src_img._new(
        src_img.im.convert("P", 1, palette_image.im)
    )  # dst_img: Image.image["P"]

    if not fast:
        dst_img.convert("RGB").show()
        reply = input("save? (*y*/n)> ")

        if reply.startswith(("n", "f")):
            sys.exit()

    dst_img.convert("RGB").save(output_pic_dest)

    pixels = dst_img.convert("RGB").load()

    data: Dict[Tuple[int, int], int] = {}

    for i in range(0, dst_img.size[0]):
        for j in range(0, dst_img.size[1]):
            data[(i + left, j + up)] = PALETTE[pixels[i, j]]

    with open(dest + ".pickle", "wb") as f:
        pickle.dump(data, f)

    with open(dest + ".json", "w") as f:
        js_data = []
        json.dump([[x, y, c] for (x, y), c in data.items()], f)
