from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.models import User

from database_models.models import Card, Profile, Company
from database_models.utils import check_hex_digit
from database_models.serializers import UserSerializer, CompanySerializer, ProfileSerializer


__all__ = ["RegisterCompany", "RegisterCard", "RegisterUser", "LoginUser", "LogoutUser"]


class RegisterUser(APIView):
    def post(self, request: Request) -> Response:
        try:
            email = request.data.get("email")

            if email is None:
                return Response(data={"success": False, "message": "Error. Incorrect request body."}, status=400)

            if User.objects.filter(email=email).count():
                return Response(data={"success": False, "message": "Error. There is user with that data."}, status=500)

            user_serializer = UserSerializer(data=request.data)
            if user_serializer.is_valid():
                user = user_serializer.save()
                profile = Profile()
                profile.user = user
                profile.telegram_chat_id = request.data.get("telegram_chat_id", "")
                profile.save()
                return Response(data={"success": True, "message": ""})
            else:
                return Response(data={"success": False, "message": "Error. Request data is not valid."}, status=400)
        except Exception as ex:
            return Response(data={"success": False, "message": f"Error. {str(ex)}"}, status=500)


class LoginUser(APIView):
    def post(self, request: Request) -> Response:
        try:
            email = request.data.get("email")
            password = request.data.get("password")

            if email is None or password is None:
                return Response(data={"success": False, "message": "Error. Incorrect request body."}, status=400)

            users = User.objects.filter(email=email)
            if not users.count():
                return Response(data={"success": False, "message": "Error. There is no user with that credentials."}, status=404)
            user = users.first()
            if not user.check_password(password):
                return Response(data={"success": False, "message": "Error. There is no user with that credentials."}, status=404)

            tokens = Token.objects.filter(user=user)
            if tokens.count() != 0:
                token = tokens.first()
            else:
                token = Token.objects.create(user=user)
            return Response(data={"success": True, "token": token.key, "message": ""})
        except Exception as ex:
            return Response(data={"success": False, "message": f"Error. {str(ex)}"}, status=500)


class LogoutUser(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        try:
            user = request.user

            token = Token.objects.get(user=user)
            token.delete()
        except Exception:
            pass
        return Response(data={"success": True, "message": ""})


class RegisterCard(APIView):  # TODO: rewrite with serializer
    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        try:
            card_uid = request.data.get("card_uid")
            if card_uid is None:
                return Response(data={"success": False, "message": "Error. Incorrect request body."}, status=400)

            if not check_hex_digit(card_uid):
                return Response(data={"success": False, "message": "Error. Incorrect card_uid."}, status=400)

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
                return Response(data={"success": False, "message": "Error. There is company with that data."}, status=500)

            company_serializer = CompanySerializer(data=request.data)
            if company_serializer.is_valid():
                company = company_serializer.save()
                company.generate_token()
                return Response(data={"success": True, "data": {"name": company.name, "company_token": company.company_token}, "message": ""})
            else:
                return Response(data={"success": False, "message": "Error. Request data is not valid."}, status=400)
        except Exception as ex:
            return Response(data={"success": False, "message": f"Error. {str(ex)}"}, status=500)


class GetUserInfo(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        try:
            user = request.user
            profiles = Profile.objects.filter(user=user)
            if profiles.count() == 0:
                return Response(data={"success": False, "message": "Error. There is no profile for this user"}, status=404)
            profile = profiles.first()

            serializer = ProfileSerializer(profile)
            return Response(data={"success": True, "data": serializer.data, "message": ""}, status=200)
        except Exception as ex:
            return Response(data={"success": False, "message": f"Error. {str(ex)}"}, status=500)
