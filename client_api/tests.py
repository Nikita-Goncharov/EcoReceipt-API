import random
from decimal import Decimal

from rest_framework.authtoken.models import Token
from django.test import TestCase, Client, RequestFactory
from django.contrib.auth.models import User

from .views import GetCardBalance
from database_models.models import Transaction, Receipt, Profile, Card, Company, IncreaseBalanceRequest


def do_user_login(email: str, password: str, username: str = "testname") -> tuple[User, str]:
    client = Client()
    user = User.objects.create(username=username, email=email)
    user.set_password(password)
    user.save()
    Profile.objects.create(user=user, telegram_chat_id="1111111")

    body = {"email": user.email, "password": password}

    response = client.post("/client_api/login/", body)
    TestCase.assertEqual(TestCase(), response.status_code, 200)
    response_data: dict = response.json()
    return user, response_data.get("token")


class RegisterUserTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = "/client_api/register_user/"

    def test_inccorrect_body(self):
        body = {
            "username": "nikname",
            "first_name": "Bob",
            "last_name": "Smith",
            "password": "password1213",
            "telegram_chat_id": "2334292",
        }

        response = self.client.post(self.url, body)
        self.assertEqual(response.status_code, 400)

    def test_correct_request(self):
        body = {
            "username": "nikname",
            "first_name": "Bob",
            "last_name": "Smith",
            "email": "admin@gmail.com",
            "password": "password1213",
            "telegram_chat_id": "2334292",
        }

        response = self.client.post(self.url, body)
        self.assertEqual(response.status_code, 200)

        profiles = Profile.objects.order_by("-created")
        self.assertNotEqual(profiles.count(), 0)

        profile = profiles.first()
        self.assertEqual(profile.user.username, body["username"])
        self.assertEqual(profile.user.first_name, body["first_name"])
        self.assertEqual(profile.user.last_name, body["last_name"])
        self.assertEqual(profile.user.email, body["email"])
        self.assertEqual(profile.telegram_chat_id, body["telegram_chat_id"])


class LoginTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = "/client_api/login/"
        self.password = "password1213"
        self.user = User.objects.create(username="testname", email="test@gmail.com")
        self.user.set_password(self.password)
        self.user.save()

    def test_incorrect_body(self):
        body = {"email": self.user.email}

        response = self.client.post(self.url, body)
        self.assertEqual(response.status_code, 400)

    def test_incorrect_body_email(self):
        body = {"email": "test111@gmail.com", "password": self.password}

        response = self.client.post(self.url, body)
        self.assertEqual(response.status_code, 404)

    def test_correct_request(self):
        body = {"email": self.user.email, "password": self.password}

        response = self.client.post(self.url, body)
        self.assertEqual(response.status_code, 200)

        tokens = Token.objects.filter(user=self.user)
        self.assertNotEqual(tokens.count(), 0)


class LogoutTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = "/client_api/logout/"
        self.user, self.user_token = do_user_login("test@gmail.com", "password1213")

    def test_incorrect_token(self):
        headers = {"Authorization": "Token 898w9735bo359"}

        response = self.client.post(self.url, headers=headers)
        self.assertEqual(response.status_code, 401)

    def test_correct_request(self):
        headers = {"Authorization": f"Token {self.user_token}"}

        response = self.client.post(self.url, headers=headers)
        self.assertEqual(response.status_code, 200)

        tokens = Token.objects.filter(user=self.user)
        self.assertEqual(tokens.count(), 0)


class RegisterCardTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = "/client_api/register_card/"
        self.user, self.user_token = do_user_login("test@gmail.com", "password1213")

    def test_incorrect_body(self):
        headers = {"Authorization": f"Token {self.user_token}"}

        body = {}

        response = self.client.post(self.url, body, headers=headers)
        self.assertEqual(response.status_code, 400)

    def test_incorrect_card_uid(self):
        headers = {"Authorization": f"Token {self.user_token}"}

        body = {"card_uid": "101010101010"}

        response = self.client.post(self.url, body, headers=headers)
        self.assertEqual(response.status_code, 400)

    def test_correct_request(self):
        headers = {"Authorization": f"Token {self.user_token}"}

        body = {"card_uid": "34abc333"}

        response = self.client.post(self.url, body, headers=headers)
        self.assertEqual(response.status_code, 200)

        cards = Card.objects.order_by("-created")
        self.assertNotEqual(cards.count(), 0)

        card = cards.first()
        self.assertEqual(card.card_uid, body["card_uid"])


class RegisterCompanyTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = "/client_api/register_company/"

    def test_inccorrect_body(self):
        body = {
            "name": "Company1",
            "hotline_phone": "+380000000000",
        }

        response = self.client.post(self.url, body)
        self.assertEqual(response.status_code, 400)

    def test_correct_request(self):
        body = {
            "name": "Company1",
            "hotline_phone": "+380000000000",
            "country": "Country",
            "city": "City",
            "street": "Street",
            "building": "12",
        }

        response = self.client.post(self.url, body)
        self.assertEqual(response.status_code, 200)

        companies = Company.objects.order_by("-created")
        self.assertNotEqual(companies.count(), 0)

        company = companies.first()
        self.assertEqual(company.name, body["name"])
        self.assertEqual(company.hotline_phone, body["hotline_phone"])

        self.assertEqual(company.country, body["country"])
        self.assertEqual(company.city, body["city"])
        self.assertEqual(company.street, body["street"])
        self.assertEqual(company.building, body["building"])

        self.assertNotEqual(company.company_token, "")


class GetUserInfoTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = "/client_api/get_user_info/"
        self.user, self.user_token = do_user_login("test@gmail.com", "password1213")

    def test_incorrect_token(self):
        headers = {"Authorization": "Token 898w9735bo359"}

        response = self.client.get(self.url, headers=headers)
        self.assertEqual(response.status_code, 401)

    def test_correct_request(self):
        headers = {"Authorization": f"Token {self.user_token}"}

        response = self.client.get(self.url, headers=headers)
        self.assertEqual(response.status_code, 200)


class IncreaseCardBalanceTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = "/client_api/increase_card_balance/"

        self.user, self.user_token = do_user_login("test@gmail.com", "password1213")
        self.user2, self.user2_token = do_user_login("test2@gmail.com", "password", username="testname2")

        self.card = Card.objects.create(owner=self.user.profile)
        self.card.card_uid = "d3a333b3"
        self.card.generate_card_number()
        self.card.generate_cvv()
        self.card.save()

    def test_incorrect_body(self):
        headers = {"Authorization": f"Token {self.user_token}"}

        body = {"amount": 10}

        response = self.client.post(self.url, body, headers=headers)
        self.assertEqual(response.status_code, 400)

    def test_incorrect_card_number(self):
        headers = {"Authorization": f"Token {self.user_token}"}

        body = {"card_number": "1", "amount": 10}

        response = self.client.post(self.url, body, headers=headers)
        self.assertEqual(response.status_code, 404)

    def test_incorrect_user(self):
        headers = {"Authorization": f"Token {self.user2_token}"}

        body = {"card_number": self.card.card_number, "amount": 10}

        response = self.client.post(self.url, body, headers=headers)
        self.assertEqual(response.status_code, 403)

    def test_correct_request(self):
        headers = {"Authorization": f"Token {self.user_token}"}

        body = {"card_number": self.card.card_number, "amount": 10}

        response = self.client.post(self.url, body, headers=headers)
        self.assertEqual(response.status_code, 200)

        cards = Card.objects.order_by("-updated")
        self.assertNotEqual(cards.count(), 0)

        card = cards.first()
        self.assertEqual(card.balance, Decimal(10))


class IncreaseCompanyBalanceTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = "/client_api/increase_company_balance/"
        self.company = Company.objects.create(
            name="Company",
            hotline_phone="+380000000000",
            country="Country",
            city="City",
            street="Street",
            building="12",
        )
        self.company.generate_token()

    def test_incorrect_body(self):
        body = {"amount": 10}

        response = self.client.post(self.url, body)
        self.assertEqual(response.status_code, 400)

    def test_incorrect_company_token(self):
        body = {"company_token": "9485n394038yt", "amount": 10}

        response = self.client.post(self.url, body)
        self.assertEqual(response.status_code, 404)

    def test_correct_request(self):
        body = {"company_token": self.company.company_token, "amount": 10}

        response = self.client.post(self.url, body)
        self.assertEqual(response.status_code, 200)

        companies = Company.objects.order_by("-updated")
        self.assertNotEqual(companies.count(), 0)

        company = companies.first()
        self.assertEqual(company.balance, Decimal(10))


class GetCardBalanceTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.factory = RequestFactory()
        self.request = self.factory.get("/dummy-url/")

        self.user, _ = do_user_login("test@gmail.com", "password1213")
        self.card = Card.objects.create(owner=self.user.profile)
        self.card.card_uid = "d3a333b3"
        self.card.balance = 10
        self.card.generate_card_number()
        self.card.generate_cvv()
        self.card.save()

    def test_incorrect_card_uid(self):
        response = GetCardBalance().get(self.request, "f334ab32")
        self.assertEqual(response.status_code, 404)

    def test_invalid_card_uid(self):
        response = GetCardBalance().get(self.request, "gggggggg")
        self.assertEqual(response.status_code, 400)

    def test_correct_request(self):
        response = GetCardBalance().get(self.request, self.card.card_uid)
        self.assertEqual(response.status_code, 200)

        card_balance = response.data.get("balance")
        self.assertEqual(self.card.balance, card_balance)


class GetUserTransactionsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = "/client_api/get_user_transactions/"

        self.user, self.user_token = do_user_login("test@gmail.com", "password1213")
        self.card = Card.objects.create(owner=self.user.profile)
        self.card.card_uid = "e3a333b3"
        self.card.balance = 1000
        self.card.generate_card_number()
        self.card.generate_cvv()
        self.card.save()

        company = Company(name="Store")
        company.save()
        for i in range(5):
            transaction = Transaction()
            transaction.card = self.card
            transaction.company = company
            transaction.receipt = Receipt()
            transaction.receipt.save()

            transaction.amount = random.randint(1, 10)

            transaction.card_balance_before = random.randint(1, 100)
            transaction.card_balance_after = transaction.card_balance_before - transaction.amount
            transaction.company_balance_before = random.randint(1, 100)
            transaction.company_balance_after = transaction.company_balance_before + transaction.amount
            transaction.save()

    def test_incorrect_token(self):
        headers = {"Authorization": "Token 898w9735bo359"}

        response = self.client.get(self.url, headers=headers)
        self.assertEqual(response.status_code, 401)

    def test_correct_request(self):
        headers = {"Authorization": f"Token {self.user_token}"}

        response = self.client.get(self.url, headers=headers)
        response_body = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response_body["results"]), 5)


class CreateIncreaseBalanceRequestTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = "/client_api/create_increase_balance_request/"

        self.user, self.user_token = do_user_login("test@gmail.com", "password1213")
        self.card = Card.objects.create(owner=self.user.profile)
        self.card.card_uid = "e3a333b3"
        self.card.balance = 1000
        self.card.generate_card_number()
        self.card.generate_cvv()
        self.card.save()

    def test_incorrect_token(self):
        headers = {"Authorization": "Token 898w9735bo359"}

        response = self.client.post(self.url, headers=headers)
        self.assertEqual(response.status_code, 401)

    def test_incorrect_card_number(self):
        headers = {"Authorization": f"Token {self.user_token}"}

        body = {"amount": 100, "card_number": "0", "message": ""}

        response = self.client.post(self.url, headers=headers, data=body)
        self.assertEqual(response.status_code, 404)

    def test_correct_request(self):
        headers = {"Authorization": f"Token {self.user_token}"}

        body = {"amount": 100, "card_number": self.card.card_number, "message": "Hello"}

        response = self.client.post(self.url, headers=headers, data=body)
        self.assertEqual(response.status_code, 200)

        balance_requests = IncreaseBalanceRequest.objects.all()
        self.assertEqual(balance_requests.count(), 1)
        balance_request = balance_requests.first()
        self.assertEqual(balance_request.request_status, "waiting")


class GetIncreaseBalanceRequestsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = "/client_api/get_increase_balance_requests/"

        self.user, self.user_token = do_user_login("test@gmail.com", "password1213")

    def test_incorrect_token(self):
        headers = {"Authorization": "Token 898w9735bo359"}

        response = self.client.get(self.url, headers=headers)
        self.assertEqual(response.status_code, 401)

    def test_forbidden_request(self):
        headers = {"Authorization": f"Token {self.user_token}"}

        response = self.client.get(self.url, headers=headers)
        self.assertEqual(response.status_code, 403)

    def test_correct_request(self):
        self.user.profile.role = "admin"
        self.user.profile.save()

        headers = {"Authorization": f"Token {self.user_token}"}

        response = self.client.get(self.url, headers=headers)
        self.assertEqual(response.status_code, 200)


class ConsiderIncreaseBalanceRequestsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = "/client_api/consider_increase_balance_request/"

        self.user, self.user_token = do_user_login("test@gmail.com", "password1213")

        self.card = Card.objects.create(owner=self.user.profile)
        self.card.card_uid = "e3a333b3"
        self.card.balance = 0
        self.card.generate_card_number()
        self.card.generate_cvv()
        self.card.save()

        self.balance_request = IncreaseBalanceRequest()
        self.balance_request.requested_money = 100
        self.balance_request.card = self.card
        self.balance_request.attached_message = "Hello"
        self.balance_request.save()

    def test_incorrect_token(self):
        headers = {"Authorization": "Token 898w9735bo359"}

        response = self.client.post(self.url, headers=headers)
        self.assertEqual(response.status_code, 401)

    def test_forbidden_request(self):
        headers = {"Authorization": f"Token {self.user_token}"}

        body = {"request_id": self.balance_request.id, "status": "accepted"}

        response = self.client.post(self.url, headers=headers, data=body)
        self.assertEqual(response.status_code, 403)

    def test_invalid_data(self):
        self.user.profile.role = "admin"
        self.user.profile.save()

        headers = {"Authorization": f"Token {self.user_token}"}

        body = {}

        response = self.client.post(self.url, headers=headers, data=body)
        self.assertEqual(response.status_code, 400)

    def test_correct_request(self):
        self.user.profile.role = "admin"
        self.user.profile.save()

        headers = {"Authorization": f"Token {self.user_token}"}

        body = {"request_id": self.balance_request.id, "status": "accepted"}

        response = self.client.post(self.url, headers=headers, data=body)
        self.assertEqual(response.status_code, 200)

        self.balance_request = IncreaseBalanceRequest.objects.first()
        self.assertEqual(self.balance_request.request_status, "accepted")

        self.card = Card.objects.first()
        self.assertEqual(self.card.balance, Decimal(100))


class GetUserCardsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = "/client_api/get_cards/"

        self.user, self.user_token = do_user_login("test@gmail.com", "password1213")

        self.card = Card.objects.create(owner=self.user.profile)
        self.card.card_uid = "e3a333b3"
        self.card.balance = 0
        self.card.generate_card_number()
        self.card.generate_cvv()
        self.card.save()

    def test_incorrect_token(self):
        headers = {"Authorization": "Token 898w9735bo359"}

        response = self.client.get(self.url, headers=headers)
        self.assertEqual(response.status_code, 401)

    def test_correct_request(self):
        headers = {"Authorization": f"Token {self.user_token}"}

        response = self.client.get(self.url, headers=headers)
        self.assertEqual(response.status_code, 200)
        response_body = response.json()
        self.assertEqual(len(response_body["data"]), 1)


# class GetUserCardsReceiptsTestCase(TestCase):
#     def setUp(self):
#         self.client = Client()
#         self.url = "/client_api/get_receipts_by_cards/"
#
#         self.user, self.user_token = do_user_login("test@gmail.com", "password1213")
#         self.card = Card.objects.create(owner=self.user.profile)
#         self.card.card_uid = "d3a333b3"
#         self.card.balance = 10
#         self.card.generate_card_number()
#         self.card.generate_cvv()
#         self.card.save()
#
#     def test_not_authorized_request(self):
#         response = self.client.get(self.url)
#         self.assertEqual(response.status_code, 401)
#
#     def test_correct_request(self):
#         headers = {
#             "Authorization": f"Token {self.user_token}"
#         }
#
#         response = self.client.get(self.url, headers=headers)
#         self.assertEqual(response.status_code, 200)
#         response_data = response.json().get("data")
#         self.assertEqual(len(response_data), 1)  # user has only one card, so we expect only one record in list
