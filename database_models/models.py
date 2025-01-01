import logging
import os
import hashlib
from random import randint
from decimal import Decimal

from django.db import models
from django.db.utils import IntegrityError
from django.contrib.auth.models import User

from .utils import check_hex_digit, get_random_goods_with_all_amount
from receipt_creation.receipt_builder import ReceiptBuilder, ReceiptData, ReceiptDataItem


class Profile(models.Model):
    ROLES = {
        "admin": "admin",
        "user": "user"
    }
    user = models.OneToOneField(to=User, on_delete=models.CASCADE, related_name="profile")
    telegram_chat_id = models.CharField(max_length=20, null=True, blank=True, default="")  # TODO: telegram user id ???
    role = models.CharField(choices=ROLES, default=ROLES["user"])
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profile: {self.user.first_name} {self.user.last_name}"


class Card(models.Model):
    _card_number = models.CharField(max_length=16, unique=True, null=True, blank=True)
    _cvv = models.CharField(max_length=3, null=True, blank=True)
    _balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    _card_uid = models.CharField(max_length=8, unique=True, null=True, blank=True)
    _pin_code = models.CharField(max_length=4, null=True, blank=True)
    owner = models.ForeignKey(to=Profile, on_delete=models.CASCADE, related_name="cards")

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
        else:
            logging.log(logging.INFO, "Error. Can`t set cvv for card")

    @property
    def card_number(self):
        return self._card_number

    @card_number.setter
    def card_number(self, value: str):
        if value.isdigit() and len(value) == 16:
            self._card_number = value
        else:
            logging.log(logging.INFO, "Error. Can`t set card_number for card")

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
            logging.log(logging.INFO, "Error. Can`t set card_uid for card")

    @property
    def pin_code(self):
        return self._pin_code

    @pin_code.setter
    def pin_code(self, value: str):
        if len(value) == 4 and value.isdigit():
            self._pin_code = value
        else:
            logging.log(logging.INFO, "Error. Can`t set pin_code for card")

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
        """ This method produces very distinct outputs for different input strings,
            and it’s generally secure against accidental collisions in typical usage scenarios

            SHA256 hash -> hex to decimal -> using mod by 12 from big int we are getting unique symbol -> floor divide int

        """

        # token should contain only with numbers(0-9) and * and #
        # token length should be 15 symbols
        allowed_chars = "0123456789#*"
        allowed_len = len(allowed_chars)

        # Create a hash of the input string using SHA256
        hash_object = hashlib.sha256(self.name.encode())  # the same input will always produce the same hash

        hex_hash = hash_object.hexdigest()
        num_hash = int(hex_hash, 16)

        # Create the unique string by mapping the number to the allowed characters
        unique_string = ''
        for _ in range(15):
            unique_string += allowed_chars[num_hash % allowed_len]
            num_hash //= allowed_len

        self._company_token = unique_string
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
            if img:
                self.img = img
                self.save()

        return self.img

    def _generate_receipt_img(self) -> str:
        try:
            year, month, day, hour, minute = self.created.year, self.created.month, self.created.day, self.created.hour, self.created.minute

            new_receipt_image_path = f"media/uploads/{year}/{month}/{day}/receipt_{year}_{month}_{day}_{hour}_{minute}.jpg"
            if not os.path.exists(os.path.dirname(new_receipt_image_path)):
                logging.log(logging.INFO, "Dirs for storing receipt created")
                os.makedirs(os.path.dirname(new_receipt_image_path))
            else:
                logging.log(logging.INFO, f"Dirs for storing receipt already created: {os.path.dirname(new_receipt_image_path)}")

            receipt_creator = ReceiptBuilder(
                "media/receipt_background.jpg",
                "media/exact_receipt.jpg",
                new_receipt_image_path
            )
            products = get_random_goods_with_all_amount(self.transaction.amount)
            products_part_height = 30 + len(products) * 25 + 5  # top border height + products height + bottom border height

            data: ReceiptData = {
                "header": {
                    "title": ReceiptDataItem(self.transaction.company.name, 70),
                    "address": ReceiptDataItem(self.transaction.company.address, 30),
                    "hotline_phone": ReceiptDataItem(self.transaction.company.hotline_phone, 30),
                    "datetime": ReceiptDataItem(self.created, 20)
                },
                "body": {
                    "products": ReceiptDataItem(products, products_part_height),
                    "amount": ReceiptDataItem(self.transaction.amount, 30)
                },
                "footer": {
                    "card_number": ReceiptDataItem(f"**** **** **** {self.transaction.card.card_number[-4:]}", 30),
                    "wish_phrase": ReceiptDataItem("THANK YOU FOR SHOPPING!", 30)
                }
            }
            logging.log(logging.INFO, f"Data for making receipt: {data}")
            receipt_creator.set_params(data)
            receipt_creator.make_receipt()
            return new_receipt_image_path.replace("media/", "")
        except Exception as ex:
            logging.log(logging.INFO, f"Error. {str(ex)}")
            return ""


class Transaction(models.Model):
    card = models.ForeignKey(to=Card, on_delete=models.DO_NOTHING, related_name="transactions")
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


class ServiceSetting(models.Model):
    class TYPES(models.TextChoices):
        INT = "int", "INT",
        TEXT = "str", "TEXT",
        BOOL = "bool", "BOOL"

    name = models.CharField(max_length=100, null=True, blank=True)
    value_type = models.CharField(max_length=100, choices=TYPES, default=TYPES.TEXT)
    value = models.CharField(max_length=200, null=True, blank=True)
    description = models.TextField(null=True, blank=True)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def get_value(self) -> int | str | bool:
        match self.value_type:
            case "int":
                return int(self.value)
            case "str":
                return str(self.value)
            case "bool":
                return bool(self.value)
            case _:
                return self.value

    def __str__(self):
        return f"Setting: {self.name}"


class IncreaseBalanceRequest(models.Model):
    STATUSES = {
        "waiting": "waiting",
        "accepted": "accepted",
        "considered": "considered",
        "denied": "denied"
    }

    requested_money = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    card = models.ForeignKey(Card, on_delete=models.CASCADE)
    attached_message = models.TextField(null=True, blank=True)
    request_status = models.CharField(choices=STATUSES, default=STATUSES["waiting"])

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Increase Balance Request: requested money - {self.requested_money}, card - {self.card.card_number}"
