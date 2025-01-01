import logging
from decimal import Decimal

from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.core.exceptions import ObjectDoesNotExist

from database_models.models import Card, Profile, Company, Transaction, IncreaseBalanceRequest
from database_models.utils import check_hex_digit
from database_models.serializers import CardSerializer, TransactionSerializer, IncreaseBalanceRequestSerializer


class IncreaseCardBalance(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        try:
            card_number = request.data.get("card_number")
            amount = request.data.get("amount", 0)
            logging.log(logging.INFO, f"Data from request - card_number: {card_number}, amount: {amount}")

            if card_number is None:
                return Response(data={"success": False, "message": "Error. There is no card_number."}, status=400)

            cards = Card.objects.filter(_card_number=card_number)
            if cards.count() == 0:
                return Response(data={"success": False, "message": "Error. There is no card with this card_number"}, status=404)

            card = cards.first()
            if request.user == card.owner.user:
                card.balance = card.balance + Decimal(amount)
                card.save()
                logging.log(logging.INFO, f"User card balance increased: {card.balance}")
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
            logging.log(logging.INFO, f"Data from request - company_token: {company_token}, amount: {amount}")

            if company_token is None:
                return Response(data={"success": False, "message": "Error. There is no company_token."}, status=400)

            companies = Company.objects.filter(_company_token=company_token)
            if companies.count() == 0:
                return Response(data={"success": False, "message": "Error. There is no company with this company_token."}, status=404)
            company = companies.first()
            company.balance = company.balance + Decimal(amount)
            company.save()
            logging.log(logging.INFO, f"{company.name} company balance increased: {company.balance}")
            return Response(data={"success": True, "message": ""})
        except Exception as ex:
            return Response(data={"success": False, "message": f"Error. {str(ex)}"}, status=500)


class GetCardBalance(APIView):  # inner view
    def get(self, request: Request, card_uid: str) -> Response:
        try:
            logging.log(logging.INFO, f"Data from url - card_uid: {card_uid}")

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
        logging.log(logging.INFO, f"args: {args}, kwargs: {kwargs}")
        return super().get_queryset(*args, **kwargs).filter(
            card__owner=self.request.user.profile
        )


class CreateIncreaseBalanceRequest(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        try:
            amount = request.data.get("amount", 0)
            card_number = request.data.get("card_number")
            message = request.data.get("message")

            logging.log(logging.INFO, f"Data from request - card_number: {card_number}, amount: {amount}, message: {message}")

            cards = Card.objects.filter(owner__user=request.user, _card_number=card_number)
            if cards.count() == 0:
                return Response(data={"success": True, "message": "Error. Card not found"}, status=404)
            card = cards.first()
            increase_balance_request = IncreaseBalanceRequest()
            increase_balance_request.requested_money = Decimal(amount)
            increase_balance_request.card = card
            increase_balance_request.attached_message = message
            increase_balance_request.save()
            logging.log(logging.INFO, f"IncreaseBalanceRequest created with id: {increase_balance_request.id}")
            return Response(data={"success": True, "message": ""}, status=200)
        except Exception as ex:
            return Response(data={"success": False, "message": f"Error. {str(ex)}"}, status=500)


class GetIncreaseBalanceRequests(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        try:
            profiles = Profile.objects.filter(user=request.user)
            if profiles.count() == 0:
                return Response(data={"success": False, "message": "Error. There is no profile for this user"}, status=404)
            profile = profiles.first()

            if profile.role != "admin":
                return Response(data={"success": False, "message": "Error. This action available only for admins"}, status=403)

            serializer = IncreaseBalanceRequestSerializer(
                IncreaseBalanceRequest.objects.filter(request_status="waiting"),
                many=True
            )
            data = serializer.data
            logging.log(
                logging.INFO,
                f"Get increase balance requests with status 'waiting': {data}"
            )

            return Response(data={"success": True, "data": data, "message": ""}, status=200)
        except Exception as ex:
            return Response(data={"success": False, "message": f"Error. {str(ex)}"}, status=500)


class ConsiderIncreaseBalanceRequests(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:  # TODO: change to PUT
        try:
            user = request.user
            profiles = Profile.objects.filter(user=user)
            if profiles.count() == 0:
                return Response(data={"success": False, "message": "Error. There is no profile for this user"},
                                status=404)
            profile = profiles.first()

            if profile.role != "admin":
                return Response(data={"success": False, "message": "Error. This action available only for admins"},
                                status=403)

            request_id = request.data.get("request_id")
            new_status = request.data.get("status")

            logging.log(logging.INFO,
                        "User has admin role")

            logging.log(logging.INFO,
                        f"Data from request - request_id: {request_id}, new_status: {new_status}")

            if request_id is None or new_status is None:
                return Response(data={"success": False, "message": "Error. Invalid request data"},
                                status=400)

            increase_requests = IncreaseBalanceRequest.objects.filter(pk=request_id, request_status="waiting")

            if increase_requests.count() == 0:
                return Response(data={"success": False, "message": "Error. There is no waiting increase balance request with that id"},
                                status=404)
            increase_request = increase_requests.first()

            if new_status != "accepted" and new_status != "denied":
                return Response(data={"success": False, "message": "Error. Incorrect status in request body"},
                                status=400)

            if new_status == "accepted":
                increase_request.card.balance = increase_request.card.balance + increase_request.requested_money
                increase_request.card.save()

            increase_request.request_status = new_status
            increase_request.save()

            logging.log(logging.INFO,
                        f"Money request considered and now status equal - {increase_request.request_status} ")

            return Response(data={"success": True, "message": ""}, status=200)
        except Exception as ex:
            return Response(data={"success": False, "message": f"Error. {str(ex)}"}, status=500)


class GetUserCards(ListAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        try:
            user = request.user

            serializer = CardSerializer(
                Card.objects.filter(owner__user=user),
                many=True
            )

            data = serializer.data

            logging.log(logging.INFO,
                        f"Getting user cards: {data} ")

            return Response(data={"success": True, "data": data, "message": ""}, status=200)
        except Exception as ex:
            return Response(data={"success": False, "message": f"Error. {str(ex)}"}, status=500)

