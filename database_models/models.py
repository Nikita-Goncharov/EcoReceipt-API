import os
import re
import json
from random import randint
from datetime import datetime
from decimal import Decimal

import cv2 as cv
import numpy as np
from django.db import models
from django.db.utils import IntegrityError
from django.contrib.auth.models import User
from PIL import Image, ImageFont, ImageDraw

from .utils import check_hex_digit, get_random_goods_with_all_amount, generate_barcode_img, BarCodeOptions


# TODO: models testing


class Profile(models.Model):  # TODO: add fields
    user = models.OneToOneField(to=User, on_delete=models.CASCADE, related_name="profile")

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.first_name} - {self.user.last_name}"


class Card(models.Model):
    _card_number = models.CharField(max_length=16, unique=True, null=True, blank=True)
    _cvv = models.CharField(max_length=3, null=True, blank=True)
    _balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    _card_uid = models.CharField(max_length=8, unique=True, null=True, blank=True)
    owner = models.ForeignKey(to=Profile, on_delete=models.CASCADE)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.card_number} - {self.owner.user.last_name}"

    @property
    def cvv(self):
        return self._cvv

    @cvv.setter
    def cvv(self, value: str):
        if value.isdigit():
            self._cvv = value

    @property
    def card_number(self):
        return self._card_number

    @card_number.setter
    def card_number(self, value: str):
        if value.isdigit() and len(value) == 16:
            self._card_number = value

    @property
    def balance(self):
        return self._balance

    @balance.setter
    def balance(self, new_balance: Decimal):
        self._balance = new_balance

    @property
    def card_uid(self):
        return self._card_uid

    @card_uid.setter
    def card_uid(self, value: str):
        if check_hex_digit(value):
            self._card_uid = value.lower()
        else:
            print("Error. ")

    def generate_cvv(self):
        self.cvv = str(randint(100, 999))
        self.save()

    def generate_card_number(self):
        for i in range(10):  # 10 times try to generate unique card_number
            try:
                self.card_number = str(randint(0000000000000000, 9999999999999999))  # from 0(amount 16) to 9(amount 16)
                self.save()
            except IntegrityError:
                pass


class Company(models.Model):
    name = models.CharField(max_length=100)
    _company_token = models.CharField(max_length=15, unique=True, null=True, blank=True)
    _balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    hotline_phone = models.CharField(max_length=20, unique=True, null=True, blank=True)
    country = models.CharField(max_length=40, unique=True, null=True, blank=True)
    city = models.CharField(max_length=40, unique=True, null=True, blank=True)
    street = models.CharField(max_length=40, unique=True, null=True, blank=True)
    building = models.CharField(max_length=10, unique=True, null=True, blank=True)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Company: {self.name}"

    @property
    def company_token(self):
        return self._company_token

    @company_token.setter
    def company_token(self, value: str):
        reg = re.compile('^[0-9]*#')  # check if value contain only with numbers(0-9) and * and #
        if reg.match(value) and len(value) == 15:
            self._company_token = value

    @property
    def balance(self):
        return self._balance

    @balance.setter
    def balance(self, new_balance: Decimal):
        self._balance = new_balance

    @property
    def address(self):
        return f"{self.country}, {self.city}, {self.street} {self.building}"


class Receipt(models.Model):
    img = models.ImageField(upload_to='uploads/%Y/%m/%d/', blank=True, null=True)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Receipt:"  # TODO:

    def get_receipt_img(self):
        if not self.img:
            img = self._generate_receipt_img()
            self.img = img
            self.save()

        return self.img

    def _generate_receipt_img(self) -> str:  # TODO: how i can sign receipts(for checking if original)
        RECEIPTS_ROOT = "uploads"

        receipt_image = Image.open("media/empty_receipt.jpg").copy()  # height: 1200 width: 800

        # Receipt corners coords in image
        receipt_corners_coords = {
            "top_left": (197, 83),
            "top_right": (603, 83),
            "bottom_left": (191, 1123),
            "bottom_right": (608, 1120),
        }
        receipt_image_width = receipt_corners_coords["top_right"][0] - receipt_corners_coords["top_left"][0]
        ox_middle_coords = receipt_corners_coords["top_left"][0] + receipt_image_width // 2

        year, month, day, hour, minute = (self.created.year,
                                          self.created.month,
                                          self.created.day,
                                          self.created.hour,
                                          self.created.minute)

        data = {
            "company_name": self.transaction.company.name,
            "company_address": self.transaction.company.address,
            "company_hotline_phone": self.transaction.company.hotline_phone,
            "random_goods_with_cost": get_random_goods_with_all_amount(self.transaction.amount),
            "amount": self.transaction.amount,
            "date_time": self.created.strftime("%d/%m/%Y, %H:%M:%S"),
            "first_name": self.transaction.card.owner.user.first_name,
            "last_name": self.transaction.card.owner.user.last_name,
            "card_number": f"**** **** **** {self.transaction.card.card_number[-4:]}",
            "phrase": "thank you for shopping!".upper()
        }

        draw = ImageDraw.Draw(receipt_image)
        monospace_header = ImageFont.truetype("../NotoSansMono-Regular.ttf", 32)  # TODO: add in static
        monospace_paragraph = ImageFont.truetype("../NotoSansMono-Regular.ttf", 12)

        # Add company name to receipt
        company_name_count_symbols, company_name_spaces_count = len(data["company_name"]), len(data["company_name"]) - 1
        # Using Mono font, every symbol width 16 px and +-3 for space between symbols
        company_name_width = company_name_count_symbols * 16 + company_name_spaces_count * 3

        next_line_oy = 20
        draw.text(
            (ox_middle_coords - company_name_width // 2, receipt_corners_coords["top_left"][1] + next_line_oy),
            data["company_name"],
            (0, 0, 0),
            font=monospace_header
        )
        next_line_oy += 70
        # TODO: add address
        draw.text(
            (receipt_corners_coords["top_left"][0] + 10, receipt_corners_coords["top_left"][1] + next_line_oy),
            f'Address: {data["company_address"]}',
            (0, 0, 0),
            font=monospace_paragraph
        )
        next_line_oy += 30
        # TODO: add phone
        draw.text(
            (receipt_corners_coords["top_left"][0] + 10, receipt_corners_coords["top_left"][1] + next_line_oy),
            f'Telephone: {data["company_hotline_phone"]}',
            (0, 0, 0),
            font=monospace_paragraph
        )
        next_line_oy += 30
        # TODO: add date and time
        draw.text(
            (receipt_corners_coords["top_left"][0] + 10, receipt_corners_coords["top_left"][1] + next_line_oy),
            f'Date and time: {data["date_time"]}',
            (0, 0, 0),
            font=monospace_paragraph
        )

        next_line_oy += 30
        # TODO: add list of bought goods
        for product_tuple in data["random_goods_with_cost"]:
            product_name, product_cost = product_tuple

            draw.text(
                (receipt_corners_coords["top_left"][0] + 10, receipt_corners_coords["top_left"][1] + next_line_oy),
                '-----------------------------------------------------',
                (0, 0, 0),
                font=monospace_paragraph
            )
            next_line_oy += 20
            draw.text(
                (receipt_corners_coords["top_left"][0] + 10, receipt_corners_coords["top_left"][1] + next_line_oy),
                f'{product_name} - {product_cost}$',
                (0, 0, 0),
                font=monospace_paragraph
            )
            next_line_oy += 20
            draw.text(
                (receipt_corners_coords["top_left"][0] + 10, receipt_corners_coords["top_left"][1] + next_line_oy),
                '-----------------------------------------------------',
                (0, 0, 0),
                font=monospace_paragraph
            )

            next_line_oy += 20

        next_line_oy += 30
        # TODO: add total sum
        draw.text(
            (receipt_corners_coords["top_left"][0] + 10, receipt_corners_coords["top_left"][1] + next_line_oy),
            '-----------------------------------------------------',
            (0, 0, 0),
            font=monospace_paragraph
        )
        next_line_oy += 20
        draw.text(
            (receipt_corners_coords["top_left"][0] + 10, receipt_corners_coords["top_left"][1] + next_line_oy),
            f'Total sum: {data["amount"]}',
            (0, 0, 0),
            font=monospace_paragraph
        )
        next_line_oy += 20
        draw.text(
            (receipt_corners_coords["top_left"][0] + 10, receipt_corners_coords["top_left"][1] + next_line_oy),
            '-----------------------------------------------------',
            (0, 0, 0),
            font=monospace_paragraph
        )
        next_line_oy += 30
        # TODO: add user card number
        draw.text(
            (receipt_corners_coords["top_left"][0] + 10, receipt_corners_coords["top_left"][1] + next_line_oy),
            f'Payment card: {data["card_number"]}',
            (0, 0, 0),
            font=monospace_paragraph
        )
        next_line_oy += 30
        # TODO: add wish phrase

        # Count width of phrase
        phrase_count_symbols, phrase_spaces_count = len(data["phrase"]), len(data["phrase"]) - 1
        phrase_width = phrase_count_symbols * 5 + phrase_spaces_count * 2

        draw.text(
            (ox_middle_coords - phrase_width // 2, receipt_corners_coords["top_left"][1] + next_line_oy),
            data["phrase"],
            (0, 0, 0),
            font=monospace_paragraph
        )

        # Generate and save barcode with custom settings
        options: BarCodeOptions = {
            "text": json.dumps(data),
            "format": "PNG",
            "font_size": 10,
            "module_width": .7,
            "module_height": 15.0,
            "quiet_zone": 1
        }

        bar_code_image_path = generate_barcode_img(
            options,
            f"media/uploads/{year}/{month}/{day}",
            "barcode.png"
        )
        # Add bar code to receipt
        bar_code = Image.open(bar_code_image_path)
        bar_code_new_width = receipt_image_width - 100
        bar_code_resize_coef = bar_code_new_width / bar_code.width

        bar_code = bar_code.resize((bar_code_new_width, int(bar_code.height * bar_code_resize_coef)))
        bar_code_middle_ox = bar_code.width // 2
        # TODO: learn how mask work
        receipt_image.paste(bar_code, (
            ox_middle_coords - bar_code_middle_ox, receipt_corners_coords["bottom_left"][1] - bar_code.height - 30),
                            bar_code)

        receipt_image_path = os.path.join("media", RECEIPTS_ROOT, str(year), str(month), str(day))

        if not os.path.exists(receipt_image_path):
            os.makedirs(receipt_image_path)

        receipt_image = np.array(receipt_image)
        cv.imwrite(os.path.join(receipt_image_path, f"receipt_{year}_{month}_{day}_{hour}_{minute}.jpg"), receipt_image)

        return os.path.join(RECEIPTS_ROOT, str(year), str(month), str(day), f"receipt_{year}_{month}_{day}_{hour}_{minute}.jpg")


class Transaction(models.Model):
    card = models.ForeignKey(to=Card, on_delete=models.DO_NOTHING)
    company = models.ForeignKey(to=Company, on_delete=models.DO_NOTHING)
    receipt = models.OneToOneField(to=Receipt, on_delete=models.CASCADE, related_name="transaction")
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    card_balance_before = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    card_balance_after = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    company_balance_before = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    company_balance_after = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Transaction: {self.card.card_number} - {self.created}"
