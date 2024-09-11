import os
import re
from random import randint
from datetime import date
from decimal import Decimal

import cv2 as cv
from django.contrib.auth.models import User
from django.db.utils import IntegrityError
from django.db import models

from .utils import check_hex_digit

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
	_card_uid = models.CharField(max_length=6, unique=True, null=True, blank=True)
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

	def _generate_receipt_img(self) -> str:
		RECEIPTS_ROOT = "uploads"

		receipt_image = cv.imread("media/empty_receipt.jpg").copy()

		# TODO: how i can sign receipts(for checking if original)
		# TODO: fill with data
		today = date.today()
		year, month, day = today.year, today.month, today.day

		receipt_image_path = os.path.join("media", RECEIPTS_ROOT, str(year), str(month), str(day))

		if not os.path.exists(receipt_image_path):
			os.makedirs(receipt_image_path)

		cv.imwrite(os.path.join(receipt_image_path, "receipt.jpg"), receipt_image)  # TODO: add time in receipt name

		return os.path.join(RECEIPTS_ROOT, str(year), str(month), str(day), "receipt.jpg")


class Transaction(models.Model):
	card = models.ForeignKey(to=Card, on_delete=models.DO_NOTHING)
	company = models.ForeignKey(to=Company, on_delete=models.DO_NOTHING)
	receipt = models.ForeignKey(to=Receipt, on_delete=models.CASCADE)

	card_balance_before = models.DecimalField(max_digits=10, decimal_places=2, default=0)
	card_balance_after = models.DecimalField(max_digits=10, decimal_places=2, default=0)

	company_balance_before = models.DecimalField(max_digits=15, decimal_places=2, default=0)
	company_balance_after = models.DecimalField(max_digits=15, decimal_places=2, default=0)

	created = models.DateTimeField(auto_now_add=True)
	updated = models.DateTimeField(auto_now=True)

	def __str__(self):
		return f"Transaction: {self.card.card_number} - {self.created}"
