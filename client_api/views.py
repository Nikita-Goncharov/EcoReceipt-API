from decimal import Decimal

from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist

from database_models.models import Card, Profile, Company
from database_models.utils import check_hex_digit
from database_models.serializers import UserSerializer, CompanySerializer, CardSerializer


class RegisterUser(APIView):
    def post(self, request: Request) -> Response:
        try:
            email = request.data.get("email")
            if User.objects.filter(email=email).count():
                return Response(data={"success": False, "message": f"Error. There is user with that data."}, status=500)

            user_serializer = UserSerializer(data=request.data)
            if user_serializer.is_valid():
                user = user_serializer.save()
                profile = Profile()
                profile.user = user
                profile.telegram_chat_id = request.data.get("telegram_chat_id", "")
                profile.save()
                return Response(data={"success": True, "message": ""})
            else:
                return Response(data={"success": False, "message": f"Error. Request data is not valid."}, status=400)
        except Exception as ex:
            return Response(data={"success": False, "message": f"Error. {str(ex)}"}, status=500)


class LoginUser(APIView):
    def post(self, request: Request) -> Response:
        try:
            email = request.data.get("email")
            password = request.data.get("password")

            users = User.objects.filter(email=email)
            if not users.count():
                return Response(data={"success": False, "message": f"Error. There is no user with that credentials."}, status=400)
            user = users.first()
            if not user.check_password(password):
                return Response(data={"success": False, "message": f"Error. There is no user with that credentials."}, status=400)

            tokens = Token.objects.filter(user=user)
            if tokens.count() != 0:
                token = tokens.first()
            else:
                token = Token.objects.create(user=user)
            return Response(data={"success": True, "token": token.key, "message": ""})
        except Exception as ex:
            return Response(data={"success": False, "message": f"Error. {str(ex)}"}, status=500)


class LogoutUser(APIView):
    def post(self, request: Request) -> Response:
        try:
            user = request.user

            token = Token.objects.get(user=user)
            token.delete()
        except Exception as ex:
            pass
        return Response(data={"success": True, "message": ""})


class RegisterCard(APIView):  # TODO: rewrite with serializer
    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        try:
            card_uid = request.data.get("card_uid")
            print(card_uid)
            user = request.user
            card = Card(owner=user.profile)
            card.generate_cvv()
            card.card_uid = card_uid
            card.generate_card_number()
            card.save()
            return Response(data={"success": True, "message": ""})
        except Exception as ex:
            return Response(data={"success": False, "message": f"Error. {str(ex)}"}, status=500)


class RegisterCompany(APIView):
    def post(self, request: Request) -> Response:
        try:
            name = request.data.get("name")
            if Company.objects.filter(name=name).count():
                return Response(data={"success": False, "message": f"Error. There is company with that data."}, status=500)

            company_serializer = CompanySerializer(data=request.data)
            if company_serializer.is_valid():
                company = company_serializer.save()
                company.generate_token()
                return Response(data={"success": True, "message": ""})
            else:
                return Response(data={"success": False, "message": f"Error. Request data is not valid."}, status=400)
        except Exception as ex:
            return Response(data={"success": False, "message": f"Error. {str(ex)}"}, status=500)


class IncreaseCardBalance(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        try:
            card_number = request.data.get("card_number")
            amount = request.data.get("amount", 0)

            if card_number is None:
                return Response(data={"success": False, "message": "Error. There is no card_number."}, status=400)

            cards = Card.objects.filter(_card_number=card_number)
            if cards.count() == 0:
                return Response(data={"success": False, "message": "Error. There is no company with this card_number"}, status=404)

            card = cards.first()
            if request.user == card.owner.user:
                card.balance = card.balance + Decimal(amount)
                card.save()
                return Response(data={"success": True, "message": ""})
            else:
                return Response(data={"success": False, "message": "Error. You are not card owner."}, status=403)
        except ObjectDoesNotExist:
            return Response(data={"success": False, "message": "Error. Card does not registered."}, status=404)


class IncreaseCompanyBalance(APIView):
    def post(self, request: Request) -> Response:
        try:
            company_token = request.data.get("company_balance")
            amount = request.data.get("amount", 0)

            if company_token is None:
                return Response(data={"success": False, "message": "Error. There is no company_token."}, status=400)

            companies = Company.objects.filter(_company_token=company_token)
            if companies.count() == 0:
                return Response(data={"success": False, "message": "Error. There is no company with this company_token."}, status=404)
            company = companies.first()
            company.balance = company.balance + Decimal(amount)
            company.save()
            return Response(data={"success": True, "message": ""})
        except ObjectDoesNotExist:
            return Response(data={"success": False, "message": "Error. Company does not registered."}, status=404)


class GetCardBalance(APIView):  # inner view
    def get(self, request: Request, card_uid: str) -> Response:
        try:
            if check_hex_digit(card_uid):
                card = Card.objects.get(_card_uid=card_uid.lower())
                return Response(data={"success": True, "balance": card.balance, "message": ""})
            else:
                return Response(data={"success": False, "message": "Error. Invalid card UID."}, status=400)
        except ObjectDoesNotExist:
            return Response(data={"success": False, "message": "Error. Card does not registered."}, status=404)


class GetUserCardsReceipts(APIView):  # TODO: sort and pagination
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, count: int = 10, page: int = 1) -> Response:
        try:
            serializer = CardSerializer(Card.objects.filter(owner=request.user.profile), many=True)
            # print(serializer.data)
            return Response(data={"success": True, "data": serializer.data, "message": ""})
        except Exception as ex:
            return Response(data={"success": False, "message": f"Error. {str(ex)}"}, status=500)


class GetReceipt(APIView):
    pass


class GetCompanyBalance(APIView):
    pass
