import re
import string
from decimal import Decimal

from django.contrib.auth.models import User
from django.db import models

# TODO: models tests


# TODO: move to utils
def check_hex_digit(hex_string: str) -> bool:
	return len(hex_string) == 8 and all((symbol in string.hexdigits) for symbol in hex_string)


class Profile(models.Model):
	# TODO: add fields
	user = models.OneToOneField(to=User, on_delete=models.CASCADE)

	def __str__(self):
		return f"{self.user.first_name} - {self.user.last_name}"


class Card(models.Model):
	_card_number = models.CharField(max_length=16, unique=True)
	_cvv = models.CharField(max_length=3, unique=True)
	_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
	_card_uid = models.CharField(max_length=20, unique=True, null=True, blank=True)
	owner = models.ForeignKey(to=Profile, on_delete=models.CASCADE)

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


class Company(models.Model):
	name = models.CharField(max_length=100)
	_company_token = models.CharField(max_length=15, unique=True, null=True, blank=True)
	balance = models.DecimalField(max_digits=15, decimal_places=2)

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


class Receipt(models.Model):
	receipt_img = models.ImageField(upload_to ='uploads/%Y/%m/%d/', blank=True, null=True)
	created = models.DateTimeField(auto_now_add=True)
	card = models.ForeignKey(to=Card, on_delete=models.DO_NOTHING)
	company = models.ForeignKey(to=Company, on_delete=models.DO_NOTHING)

	def __str__(self):
		return f"Receipt: {self.card.card_number} - {self.created}"

	def get_receipt_img(self):
		if not self.receipt_img:
			img = self.__generate_receipt_img()
			self.receipt_img = img
		
		return self.receipt_img

	def __generate_receipt_img(self):
		# TODO: how i can sign receipts(for checking if original)
		pass  # TODO: generate fill empty receipt image using opencv
