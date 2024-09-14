import os
import string
from random import randint
from decimal import Decimal
from typing import TypedDict

import barcode
import cv2 as cv
import numpy as np
from barcode.writer import ImageWriter


class BarCodeOptions(TypedDict):
    text: str  # all data about receipt
    format: str  # 'PNG'
    font_size: int  # 10
    module_width: float  # .7
    module_height: float  # 15
    quiet_zone: int  # 1 TODO: read about it


def check_hex_digit(hex_string: str) -> bool:
    return len(hex_string) == 8 and all((symbol in string.hexdigits) for symbol in hex_string)


def generate_barcode_img(options: BarCodeOptions, path: str, image_name: str) -> str:
    ean = barcode.get('ean13', '091487112432', writer=ImageWriter())
    filename = ean.save(os.path.join(path, image_name), options=options)  # TODO: check if path exists

    # Do transparent background
    image = cv.imread(filename)
    h, w, c = image.shape
    image_bgra = np.concatenate([image, np.full((h, w, 1), 255, dtype=np.uint8)], axis=-1)
    white = np.all(image == [255, 255, 255], axis=-1)
    image_bgra[white, -1] = 0
    cv.imwrite(filename, image_bgra)

    return filename


# TODO: replace with Product model
def get_random_goods_with_all_amount(amount: Decimal) -> list[tuple[str, int]]:
    goods_list = [  # TODO: create Product model and add goods for every company (goods and services)
        "Laptop", "Smartphone", "Headphones", "Keyboard", "Mouse", "Monitor", "Printer",
        "Tablet", "Smartwatch", "Camera", "Speaker", "USB Drive", "External Hard Drive",
        "Wireless Charger", "Fitness Tracker", "Gaming Console", "Bluetooth Adapter",
        "Projector", "Webcam", "Graphics Card"
    ]

    goods_with_cost = []
    remaining_sum = int(amount)

    while remaining_sum > 0:
        cost = randint(1, remaining_sum)
        index = randint(0, len(goods_list)-1)
        goods_with_cost.append((goods_list[index], cost))
        remaining_sum -= cost

    return goods_with_cost
