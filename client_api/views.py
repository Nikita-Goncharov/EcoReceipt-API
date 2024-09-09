from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.core.exceptions import ObjectDoesNotExist

from database_models.models import Card, Profile
from database_models.utils import check_hex_digit
from database_models.serializers import UserSerializer


class RegisterUser(APIView):
    def post(self, request: Request) -> Response:
        try:
            user_serializer = UserSerializer(data=request.data)
            if user_serializer.is_valid():  # TODO: check if already exists
                user = user_serializer.save()
                profile = Profile()
                profile.user = user
                profile.save()
                return Response(data={"success": True, "message": ""})
            else:
                return Response(data={"success": False, "message": f"Error. Request data is not valid."}, status=400)
        except Exception as ex:
            return Response(data={"success": False, "message": f"Error. {str(ex)}"}, status=500)

# TODO: Login user
# TODO: Logout user
# TODO: Register card

class RegisterCard(APIView):
    def post(self, request: Request) -> Response:
        pass


class GetCardBalance(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, card_uid: str) -> Response:
        try:
            if check_hex_digit(card_uid):
                card = Card.objects.get(_card_uid=card_uid.lower())  # TODO: check if request.user it is card owner
                return Response(data={"success": True, "balance": card.balance, "message": ""})
            else:
                return Response(data={"success": False, "message": "Error. Invalid card UID."}, status=400)
        except ObjectDoesNotExist:
            return Response(data={"success": False, "message": "Error. Card does not registered."}, status=404)


class GetCompanyBalance(APIView):
    pass
