import os
from typing import TypedDict

import barcode
import cv2 as cv
import numpy as np
from PIL import Image
from barcode.writer import ImageWriter


class BarCodeOptions(TypedDict):
    text: str  # all data about receipt
    format: str  # 'PNG'
    font_size: int  # 10
    module_width: float  # .7
    module_height: float  # 15
    quiet_zone: int  # 1 TODO: read about it


def generate_barcode_img(options: BarCodeOptions, filename_path: str) -> Image:
    if os.path.exists(os.path.dirname(filename_path)):
        ean = barcode.get("ean13", "091487112432", writer=ImageWriter())
        filename = ean.save(filename_path, options=options)

        # Do transparent background
        image = cv.imread(filename)
        h, w = image.shape[:2]
        image_bgra = np.concatenate([image, np.full((h, w, 1), 255, dtype=np.uint8)], axis=-1)
        white = np.all(image == [255, 255, 255], axis=-1)
        image_bgra[white, -1] = 0
        cv.imwrite(filename, image_bgra)

        return Image.open(filename)
