import string
from decimal import Decimal

from django.db import models
from django.test import TestCase
from django.contrib.auth.models import User

from .models import Profile, Card, Company, Product, Receipt, Transaction, ServiceSetting, IncreaseBalanceRequest


def check_created_updated_fields(instance: models.Model):
    TestCase.assertTrue(TestCase(), hasattr(instance, "created"))
    TestCase.assertTrue(TestCase(), hasattr(instance, "updated"))


class ProfileTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="testname", email="test@gmail.com")
        self.profile = Profile.objects.create(user=self.user, telegram_chat_id="1111111")

    def test_profile_values(self):
        self.assertEqual(self.profile.user, self.user)
        self.assertEqual(self.profile.telegram_chat_id, "1111111")

    def test_telegram_chat_id_max_length(self):
        max_length = self.profile._meta.get_field("telegram_chat_id").max_length
        self.assertEqual(max_length, 20)

    def test_created_updated_fields(self):
        check_created_updated_fields(self.profile)


class CardTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="testname", email="test@gmail.com")
        self.profile = Profile.objects.create(user=self.user, telegram_chat_id="1111111")
        self.card = Card.objects.create(owner=self.profile)
        self.card.generate_cvv()
        self.card.generate_card_number()
        self.card.card_uid = "b2af5522"
        self.card.save()

    def test_card_values(self):
        self.assertEqual(self.card.owner, self.profile)

        self.assertEqual(len(self.card.cvv), 3)
        for symbol in self.card.cvv:
            self.assertIn(symbol, string.digits)

        self.assertEqual(len(self.card.card_number), 16)
        for symbol in self.card.card_number:
            self.assertIn(symbol, string.digits)

        self.assertEqual(len(self.card.card_uid), 8)
        for symbol in self.card.card_uid:
            self.assertIn(symbol, string.hexdigits)

        self.assertEqual(self.card.balance, Decimal(0))

    def test_cvv_card_uid_card_number_max_length(self):
        cvv_max_length = self.card._meta.get_field("_cvv").max_length
        card_uid_max_length = self.card._meta.get_field("_card_uid").max_length
        card_number_max_length = self.card._meta.get_field("_card_number").max_length

        self.assertEqual(cvv_max_length, 3)
        self.assertEqual(card_uid_max_length, 8)
        self.assertEqual(card_number_max_length, 16)

    def test_created_updated_fields(self):
        check_created_updated_fields(self.card)


class CompanyTestCase(TestCase):
    def setUp(self):
        self.company = Company.objects.create(
            name="Company",
            hotline_phone="+380000000000",
            country="Country",
            city="City",
            street="Street",
            building="12"
        )
        self.company.generate_token()

    def test_company_values(self):
        self.assertEqual(self.company.name, "Company")
        self.assertEqual(self.company.hotline_phone, "+380000000000")

        self.assertEqual(self.company.country, "Country")
        self.assertEqual(self.company.city, "City")
        self.assertEqual(self.company.street, "Street")
        self.assertEqual(self.company.building, "12")

        self.assertEqual(len(self.company.company_token), 15)
        for symbol in self.company.company_token:
            self.assertIn(symbol, string.digits + "*#")

    def test_company_token_max_length(self):
        max_length = self.company._meta.get_field("_company_token").max_length
        self.assertEqual(max_length, 15)

    def test_name(self):
        max_length = self.company._meta.get_field("name").max_length
        unique = self.company._meta.get_field("name").unique

        self.assertTrue(unique)
        self.assertEqual(max_length, 100)

    def test_company_address(self):
        country_max_length = self.company._meta.get_field("country").max_length
        city_max_length = self.company._meta.get_field("city").max_length
        street_max_length = self.company._meta.get_field("street").max_length
        building_max_length = self.company._meta.get_field("building").max_length

        self.assertEqual(country_max_length, 40)
        self.assertEqual(city_max_length, 40)
        self.assertEqual(street_max_length, 40)
        self.assertEqual(building_max_length, 10)
        self.assertEqual(self.company.address, "Country, City, Street 12")

    def test_created_updated_fields(self):
        check_created_updated_fields(self.company)


class ProductTestCase(TestCase):
    def setUp(self):
        self.company = Company.objects.create(
            name="Company",
            hotline_phone="+380000000000",
            country="Country",
            city="City",
            street="Street",
            building="12"
        )
        self.product = Product.objects.create(name="Product1", description="Description", company_owner=self.company)

    def test_product_values(self):
        self.assertEqual(self.product.company_owner, self.company)
        self.assertEqual(self.product.name, "Product1")
        self.assertEqual(self.product.description, "Description")

        self.assertEqual(self.product.cost, Decimal(0))

    def test_name_max_length(self):
        max_length = self.product._meta.get_field("name").max_length
        self.assertEqual(max_length, 100)

    def test_created_updated_fields(self):
        check_created_updated_fields(self.product)


class ReceiptTestCase(TestCase):
    def setUp(self):
        self.receipt = Receipt.objects.create()

    def test_receipt_values(self):
        self.assertEqual(str(self.receipt.img), "")

    def test_created_updated_fields(self):
        check_created_updated_fields(self.receipt)


class TransactionTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="testname", email="test@gmail.com")
        self.profile = Profile.objects.create(user=self.user, telegram_chat_id="1111111")
        self.card = Card.objects.create(owner=self.profile)
        self.card.generate_cvv()
        self.card.generate_card_number()
        self.card.card_uid = "b2af5522"
        self.card.save()

        self.company = Company.objects.create(
            name="Company",
            hotline_phone="+380000000000",
            country="Country",
            city="City",
            street="Street",
            building="12"
        )

        self.receipt = Receipt.objects.create()

        self.transaction = Transaction()
        self.transaction.card = self.card
        self.transaction.company = self.company
        self.transaction.receipt = self.receipt
        self.transaction.amount = 5

        self.transaction.card_balance_before = 100
        # self.transaction.card_balance_after = zero
        # self.transaction.company_balance_before = zero
        # self.transaction.company_balance_after = zero
        self.transaction.save()

    def test_transaction_values(self):
        self.assertEqual(self.transaction.card, self.card)
        self.assertEqual(self.transaction.receipt, self.receipt)
        self.assertEqual(self.transaction.company, self.company)

        self.assertEqual(self.transaction.amount, 5)
        self.assertEqual(self.transaction.card_balance_before, 100)

        self.assertEqual(self.transaction.card_balance_after, 0)
        self.assertEqual(self.transaction.company_balance_before, 0)
        self.assertEqual(self.transaction.company_balance_after, 0)

    def test_created_updated_fields(self):
        check_created_updated_fields(self.transaction)


class ServiceSettingTestCase(TestCase):
    def setUp(self):
        self.setting = ServiceSetting.objects.create(
            name="Setting1",
            value="10",
            description="Description 1"
        )

        self.setting1 = ServiceSetting.objects.create(
            name="Setting2",
            value="11",
            value_type="int",
            description="Description 2"
        )

    def test_service_setting_values(self):
        self.assertEqual(self.setting.name, "Setting1")
        self.assertEqual(self.setting.value_type, "str")
        self.assertEqual(self.setting.value, "10")
        self.assertEqual(self.setting.description, "Description 1")
        self.assertEqual(type(self.setting.get_value()), str)

        self.assertEqual(type(self.setting1.get_value()), int)
        self.assertEqual(self.setting1.get_value(), 11)

    def test_name_value_value_type_max_length(self):
        name_max_length = self.setting._meta.get_field("name").max_length
        value_type_max_length = self.setting._meta.get_field("value_type").max_length
        value_max_length = self.setting._meta.get_field("value").max_length

        self.assertEqual(name_max_length, 100)
        self.assertEqual(value_type_max_length, 100)
        self.assertEqual(value_max_length, 200)

    def test_created_updated_fields(self):
        check_created_updated_fields(self.setting)


class IncreaseBalanceRequestTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="testname", email="test@gmail.com")
        self.profile = Profile.objects.create(user=self.user, telegram_chat_id="1111111")

        self.balance_request = IncreaseBalanceRequest()
        self.balance_request.requested_money = 20

        self.balance_request.card = Card(owner=self.profile)
        self.balance_request.card.generate_cvv()
        self.balance_request.card.generate_card_number()
        self.balance_request.card.card_uid = "b2af5522"
        self.balance_request.card.save()

        self.balance_request.attached_message = "Hello"
        self.balance_request.save()

    def test_balance_request_values(self):
        self.assertEqual(self.balance_request.requested_money, Decimal(20))
        self.assertEqual(self.balance_request.attached_message, "Hello")
        self.assertEqual(self.balance_request.request_status, "waiting")

    def test_requested_money(self):
        max_digits_count = self.balance_request._meta.get_field("requested_money").max_digits
        decimal_places = self.balance_request._meta.get_field("requested_money").decimal_places

        self.assertEqual(max_digits_count, 10)
        self.assertEqual(decimal_places, 2)

    def test_status_changing(self):
        self.balance_request.request_status = "accepted"
        self.balance_request.save()

        self.assertEqual(self.balance_request.request_status, "accepted")

    def test_created_updated_fields(self):
        check_created_updated_fields(self.balance_request)
