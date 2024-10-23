from decimal import Decimal

from rest_framework.request import Request
from rest_framework.authtoken.models import Token
from django.test import TestCase, Client, RequestFactory
from django.contrib.auth.models import User

from .views import GetCardBalance
from database_models.models import Profile, Card, Company


def do_user_login(email: str, password: str, username: str = "testname") -> tuple[User, str]:
    client = Client()
    user = User.objects.create(username=username, email=email)
    user.set_password(password)
    user.save()
    profile = Profile.objects.create(user=user, telegram_chat_id="1111111")

    body = {
        "email": user.email,
        "password": password
    }

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
            "telegram_chat_id": "2334292"
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
            "telegram_chat_id": "2334292"
        }

        response = self.client.post(self.url, body)
        self.assertEqual(response.status_code, 200)

        profiles = Profile.objects.order_by('-created')
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
        body = {
            "email": self.user.email
        }

        response = self.client.post(self.url, body)
        self.assertEqual(response.status_code, 400)

    def test_incorrect_body_email(self):
        body = {
            "email": "test111@gmail.com",
            "password": self.password
        }

        response = self.client.post(self.url, body)
        self.assertEqual(response.status_code, 404)

    def test_correct_request(self):
        body = {
            "email": self.user.email,
            "password": self.password
        }

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
        headers = {
            "Authorization": "Token 898w9735bo359"
        }

        response = self.client.post(self.url, headers=headers)
        self.assertEqual(response.status_code, 401)

    def test_correct_request(self):
        headers = {
            "Authorization": f"Token {self.user_token}"
        }

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
        headers = {
            "Authorization": f"Token {self.user_token}"
        }

        body = {}

        response = self.client.post(self.url, body, headers=headers)
        self.assertEqual(response.status_code, 400)

    def test_incorrect_card_uid(self):
        headers = {
            "Authorization": f"Token {self.user_token}"
        }

        body = {
            "card_uid": "gggggggggggg"
        }

        response = self.client.post(self.url, body, headers=headers)
        self.assertEqual(response.status_code, 400)

    def test_correct_request(self):
        headers = {
            "Authorization": f"Token {self.user_token}"
        }

        body = {
            "card_uid": "34abc333"
        }

        response = self.client.post(self.url, body, headers=headers)
        self.assertEqual(response.status_code, 200)

        cards = Card.objects.order_by('-created')
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
            "building": "12"
        }

        response = self.client.post(self.url, body)
        self.assertEqual(response.status_code, 200)

        companies = Company.objects.order_by('-created')
        self.assertNotEqual(companies.count(), 0)

        company = companies.first()
        self.assertEqual(company.name, body["name"])
        self.assertEqual(company.hotline_phone, body["hotline_phone"])

        self.assertEqual(company.country, body["country"])
        self.assertEqual(company.city, body["city"])
        self.assertEqual(company.street, body["street"])
        self.assertEqual(company.building, body["building"])

        self.assertNotEqual(company.company_token, "")


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
        headers = {
            "Authorization": f"Token {self.user_token}"
        }

        body = {
            "amount": 10
        }

        response = self.client.post(self.url, body, headers=headers)
        self.assertEqual(response.status_code, 400)

    def test_incorrect_card_number(self):
        headers = {
            "Authorization": f"Token {self.user_token}"
        }

        body = {
            "card_number": "1",
            "amount": 10
        }

        response = self.client.post(self.url, body, headers=headers)
        self.assertEqual(response.status_code, 404)

    def test_incorrect_user(self):
        headers = {
            "Authorization": f"Token {self.user2_token}"
        }

        body = {
            "card_number": self.card.card_number,
            "amount": 10
        }

        response = self.client.post(self.url, body, headers=headers)
        self.assertEqual(response.status_code, 403)

    def test_correct_request(self):
        headers = {
            "Authorization": f"Token {self.user_token}"
        }

        body = {
            "card_number": self.card.card_number,
            "amount": 10
        }

        response = self.client.post(self.url, body, headers=headers)
        self.assertEqual(response.status_code, 200)

        cards = Card.objects.order_by('-updated')
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
            building="12"
        )
        self.company.generate_token()

    def test_incorrect_body(self):
        body = {
            "amount": 10
        }

        response = self.client.post(self.url, body)
        self.assertEqual(response.status_code, 400)

    def test_incorrect_company_token(self):
        body = {
            "company_token": "9485n394038yt",
            "amount": 10
        }

        response = self.client.post(self.url, body)
        self.assertEqual(response.status_code, 404)

    def test_correct_request(self):
        body = {
            "company_token": self.company.company_token,
            "amount": 10
        }

        response = self.client.post(self.url, body)
        self.assertEqual(response.status_code, 200)

        companies = Company.objects.order_by('-updated')
        self.assertNotEqual(companies.count(), 0)

        company = companies.first()
        self.assertEqual(company.balance, Decimal(10))


class GetCardBalanceTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.factory = RequestFactory()
        self.request = self.factory.get('/dummy-url/')

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
