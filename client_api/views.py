from decimal import Decimal

from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.core.exceptions import ObjectDoesNotExist

from .auth_views import *
from database_models.models import Card, Company, Transaction
from database_models.utils import check_hex_digit
from database_models.serializers import CardSerializer, TransactionSerializer


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
                return Response(data={"success": False, "message": "Error. There is no card with this card_number"}, status=404)

            card = cards.first()
            if request.user == card.owner.user:
                card.balance = card.balance + Decimal(amount)
                card.save()
                return Response(data={"success": True, "message": ""})
            else:
                return Response(data={"success": False, "message": "Error. You are not card owner."}, status=403)
        except Exception as ex:
            return Response(data={"success": False, "message": f"Error. {str(ex)}"}, status=500)


class IncreaseCompanyBalance(APIView):
    def post(self, request: Request) -> Response:
        try:
            company_token = request.data.get("company_token")
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
        except Exception as ex:
            return Response(data={"success": False, "message": f"Error. {str(ex)}"}, status=500)


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


# class GetCompanyBalance(APIView):  # inner view
#     def get(self, request: Request, company_token: str) -> Response:
#         try:
#             company = Company.objects.get(_company_token=company_token)
#             return Response(data={"success": True, "balance": company.balance, "message": ""})
#         except ObjectDoesNotExist:
#             return Response(data={"success": False, "message": "Error. Company does not registered."}, status=404)


# class GetUserCardsReceipts(APIView):  # TODO: sort and pagination
#     permission_classes = [IsAuthenticated]
#
#     def get(self, request: Request, count: int = 10, page: int = 1) -> Response:
#         try:
#             serializer = CardSerializer(Card.objects.filter(owner=request.user.profile), many=True)
#             return Response(data={"success": True, "data": serializer.data, "message": ""})
#         except Exception as ex:
#             return Response(data={"success": False, "message": f"Error. {str(ex)}"}, status=500)


class GetUserTransactions(ListAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Transaction.objects.all().order_by("-created")
    serializer_class = TransactionSerializer
    pagination_class = LimitOffsetPagination

    def get_queryset(self, *args, **kwargs):
        print(args, kwargs)
        return super().get_queryset(*args, **kwargs).filter(
            card__owner=self.request.user.profile
        )


# class GetUserCards(ListAPIView):
#     permission_classes = [IsAuthenticated]
#     queryset = Card.objects.all()
#     serializer_class = CardSerializer
#     pagination_class = LimitOffsetPagination
#
#     def get_queryset(self, *args, **kwargs):
#         return super().get_queryset(*args, **kwargs).filter(
#             owner=self.request.user.profile
#         )


# class GetReceipt(APIView):
#     pass
