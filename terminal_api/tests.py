import os
from decimal import Decimal

from django.test import TestCase, Client
from django.contrib.auth.models import User

from database_models.models import Profile, Card, Company, Transaction


class WriteOffMoneyViewTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = "/terminal_api/write_off_money/"

        self.user = User.objects.create(username="testname", email="test@gmail.com")
        self.profile = Profile.objects.create(user=self.user, telegram_chat_id="1111111")
        self.card = Card.objects.create(owner=self.profile)
        self.card.generate_cvv()
        self.card.generate_card_number()
        self.card.card_uid = "b2af5522"
        self.card.balance = 100
        self.card.save()

        self.company = Company.objects.create(
            name="Company",
            hotline_phone="+380000000000",
            country="Ukraine",
            city="Kharkiv",
            street="Sumska",
            building="12",
        )
        self.company.generate_token()

    def test_incorrect_request_body(self):
        body = {"amount": 10, "company_token": self.company.company_token}
        response = self.client.post(self.url, body)
        self.assertEqual(response.status_code, 400)

    def test_incorrect_card_uid(self):
        body = {"card_uid": "2eso32i", "amount": 10, "company_token": self.company.company_token}
        response = self.client.post(self.url, body)

        self.assertEqual(response.status_code, 404)

    def test_low_balance(self):
        body = {"card_uid": self.card.card_uid, "amount": 999_999_999, "company_token": self.company.company_token}
        response = self.client.post(self.url, body)

        self.assertEqual(response.status_code, 400)

    def test_incorrect_company_token(self):
        body = {"card_uid": self.card.card_uid, "amount": 10, "company_token": "1"}
        response = self.client.post(self.url, body)
        self.assertEqual(response.status_code, 404)

    def test_correct_request(self):
        body = {"card_uid": self.card.card_uid, "amount": 10, "company_token": self.company.company_token}
        response = self.client.post(self.url, body)
        response_data = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(response_data.get("transaction_id", None), None)

        transaction_id = response_data["transaction_id"]
        transactions = Transaction.objects.filter(id=transaction_id)
        self.assertNotEqual(transactions.count(), 0)

        transaction = transactions.first()
        self.assertEqual(transaction.card, self.card)
        self.assertEqual(transaction.company, self.company)
        self.assertNotEqual(str(transaction.receipt.img), "")

        self.assertEqual(transaction.amount, Decimal(10))
        self.assertEqual(transaction.card_balance_before, Decimal(100))
        self.assertEqual(transaction.card_balance_after, Decimal(90))

        self.assertEqual(transaction.company_balance_before, Decimal(0))
        self.assertEqual(transaction.company_balance_after, Decimal(10))

        # Removing receipt and barcode image after tests
        receipt_path = f"media/{transaction.receipt.img}"
        barcode_path = str(transaction.receipt.img).replace("receipt", "barcode").replace("jpg", "png.png")
        barcode_path = f"media/{barcode_path}"

        os.remove(receipt_path)
        os.remove(barcode_path)
