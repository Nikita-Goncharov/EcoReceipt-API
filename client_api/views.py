from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response
from django.core.exceptions import ObjectDoesNotExist
from database_models.models import Card, check_hex_digit

# TODO: add serializer for check and maybe for other models


class GetCardBalance(APIView):

    def get(self, request: Request, card_uid: str):  # TODO: add auth
        if check_hex_digit(card_uid):
            try:
                card = Card.objects.get(_card_uid=card_uid.lower())
                return Response(data={"success": True, "balance": card.balance, "message": ""})
            except ObjectDoesNotExist:
                return Response(data={"success": False, "message": "Error. Card does not registered."}, status=404)
        else:
            return Response(data={"success": False, "message": "Error. Invalid card UID."}, status=400)


class GetCompanyBalance(APIView):
    pass
