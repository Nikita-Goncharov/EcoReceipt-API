import os
from random import randint
from decimal import Decimal

from django.db import models
from django.db.utils import IntegrityError
from django.contrib.auth.models import User

from .utils import check_hex_digit, get_random_goods_with_all_amount
from receipt_creation.receipt_builder import ReceiptBuilder, ReceiptCornerCoords, Coords, ReceiptData

# TODO: models testing


class Profile(models.Model):  # TODO: add fields
    user = models.OneToOneField(to=User, on_delete=models.CASCADE, related_name="profile")
    telegram_chat_id = models.CharField(max_length=20, null=True, blank=True, default="")  # TODO: telegram user id ???

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profile: {self.user.first_name} {self.user.last_name}"


class Card(models.Model):
    _card_number = models.CharField(max_length=16, unique=True, null=True, blank=True)
    _cvv = models.CharField(max_length=3, null=True, blank=True)
    _balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    _card_uid = models.CharField(max_length=8, unique=True, null=True, blank=True)
    owner = models.ForeignKey(to=Profile, on_delete=models.CASCADE)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Card: {self.card_number}"

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
    name = models.CharField(max_length=100, unique=True)
    _company_token = models.CharField(max_length=15, unique=True, null=True, blank=True)
    _balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    hotline_phone = models.CharField(max_length=20, unique=True, null=True, blank=True)
    country = models.CharField(max_length=40, null=True, blank=True)
    city = models.CharField(max_length=40, null=True, blank=True)
    street = models.CharField(max_length=40, null=True, blank=True)
    building = models.CharField(max_length=10, null=True, blank=True)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Company: {self.name}"

    @property
    def company_token(self):
        return self._company_token

    @property
    def balance(self):
        return self._balance

    @balance.setter
    def balance(self, new_balance: Decimal):
        self._balance = new_balance

    @property
    def address(self):
        return f"{self.country}, {self.city}, {self.street} {self.building}"

    def generate_token(self):
        # token should contain only with numbers(0-9) and * and #
        # token length should be 15 symbols
        valid_token_symbols = "0123456789*#"
        token = ""
        for i in range(0, 15):
            index = randint(0, len(valid_token_symbols)-1)
            token = valid_token_symbols[index]

        self._company_token = token
        self.save()


class Product(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)
    cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    company_owner = models.ForeignKey(to=Company, on_delete=models.CASCADE, related_name="products")

    def __str__(self):
        return f"Product: {self.name}"


class Receipt(models.Model):
    img = models.ImageField(upload_to='uploads/%Y/%m/%d/', blank=True, null=True)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Receipt: {self.img}"

    def get_receipt_img(self):
        if not self.img:
            img = self._generate_receipt_img()
            self.img = img
            self.save()

        return self.img

    def _generate_receipt_img(self) -> str:  # TODO: how i can sign receipts(for checking if original)
        try:
            year, month, day, hour, minute = self.created.year, self.created.month, self.created.day, self.created.hour, self.created.minute

            new_receipt_image_path = f"media/uploads/{year}/{month}/{day}/receipt_{year}_{month}_{day}_{hour}_{minute}.jpg"
            if not os.path.exists(os.path.dirname(new_receipt_image_path)):
                os.makedirs(os.path.dirname(new_receipt_image_path))

            receipt_creator = ReceiptBuilder(
                "media/empty_receipt.jpg",
                new_receipt_image_path
            )

            data: ReceiptData = {
                "header": {
                    "title": self.transaction.company.name,
                    "address": self.transaction.company.address,
                    "hotline_phone": self.transaction.company.hotline_phone,
                    "datetime": self.created
                },
                "body": {
                    "products": get_random_goods_with_all_amount(self.transaction.amount),
                    "amount": self.transaction.amount,
                },
                "footer": {
                    "card_number": f"**** **** **** {self.transaction.card.card_number[-4:]}",
                    "wish_phrase": "THANK YOU FOR SHOPPING!"
                }
            }

            receipt_corners_coords: ReceiptCornerCoords = {
                "top_left": Coords(197, 83),
                "top_right": Coords(603, 83),
                "bottom_left": Coords(191, 1123),
                "bottom_right": Coords(608, 1120),
            }

            receipt_creator.set_params(data, receipt_corners_coords)
            receipt_creator.make_receipt()
            return new_receipt_image_path.replace("media/", "")
        except Exception as ex:
            print(f"Error. {str(ex)}")
            return ""


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
        return f"Transaction: {self.card.card_number}"
