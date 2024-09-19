# import os
import string
from random import randint
from decimal import Decimal


def check_hex_digit(hex_string: str) -> bool:
    return len(hex_string) == 8 and all((symbol in string.hexdigits) for symbol in hex_string)


# TODO: replace with Product model
def get_random_goods_with_all_amount(amount: Decimal) -> list[tuple[str, Decimal]]:
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
        goods_with_cost.append((goods_list[index], Decimal(cost)))
        remaining_sum -= cost

    return goods_with_cost
