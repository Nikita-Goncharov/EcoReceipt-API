from decimal import Decimal

from django.db import transaction as django_transaction
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.views import APIView

from client_api.views import GetCardBalance
from database_models.models import Card, Company, Receipt, Transaction


# TODO: in error responses add error_code for terminal for error show on lcd
class WriteOffMoney(APIView):

    @django_transaction.atomic
    def post(self, request: Request):
        try:
            card_uid = request.data.get("card_uid")
            write_off_amount = request.data.get("amount")
            company_token = request.data.get("company_token")

            if card_uid is None or write_off_amount is None or company_token is None:
                return Response(data={"success": False, "message": "Error. Incorrect request body."}, status=400)

            # requests.get(f"http://localhost:8000/client_api/get_card_balance/{card_uid}")
            response = GetCardBalance().get(request=request, card_uid=card_uid)
            if response.status_code != 200:
                return Response(data={"success": False, "message": f"Error. Card UID is incorrect."}, status=404)

            card_current_balance = response.data["balance"]
            if card_current_balance < write_off_amount:  # Check if card balance bigger then write off sum
                return Response(
                    data={"success": False, "message": f"Error. Card balance lower than write off sum."},
                    status=404
                )

            companies = Company.objects.filter(_company_token=company_token)
            if not companies.count():  # Check if company registered in system
                return Response(
                    data={"success": False, "message": f"Error. There is no registered company with this token."},
                    status=404
                )

            card = Card.objects.get(_card_uid=card_uid)
            company = companies.first()

            transaction = Transaction()
            transaction.card = card
            transaction.company = company

            transaction.receipt = Receipt()
            transaction.receipt.save()
            transaction.amount = write_off_amount
            transaction.card_balance_before = card.balance
            transaction.company_balance_before = company.balance

            card.balance = card.balance - Decimal(write_off_amount)
            company.balance = company.balance + Decimal(write_off_amount)

            card.save()
            company.save()

            transaction.card_balance_after = card.balance
            transaction.company_balance_after = company.balance
            transaction.save()

            transaction.receipt.get_receipt_img()
            return Response(data={"success": True, "transaction_id": transaction.id, "message": ""}, status=200)
        except Exception as ex:
            return Response(data={"success": False, "message": f"Error. {str(ex)}."}, status=500)