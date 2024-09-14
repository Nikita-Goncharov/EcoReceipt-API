from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist

from database_models.models import Card, Profile
from database_models.utils import check_hex_digit
from database_models.serializers import UserSerializer


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


class RegisterCard(APIView):
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


# TODO: view for adding money on balance card and company

class GetCardBalance(APIView):
    def get(self, request: Request, card_uid: str) -> Response:
        try:
            if check_hex_digit(card_uid):
                card = Card.objects.get(_card_uid=card_uid.lower())
                # if card.owner == request.user:  # TODO: check if request.user it is card owner
                return Response(data={"success": True, "balance": card.balance, "message": ""})
            else:
                return Response(data={"success": False, "message": "Error. Invalid card UID."}, status=400)
        except ObjectDoesNotExist:
            return Response(data={"success": False, "message": "Error. Card does not registered."}, status=404)


class GetCompanyBalance(APIView):
    pass
