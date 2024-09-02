from decimal import Decimal

import requests
from django.db import transaction
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.views import APIView

from database_models.models import Card, Company, Receipt


class WriteOffMoney(APIView):
    def post(self, request: Request):
        try:
            card_uid = request.data.get("card_uid")
            write_off_amount = request.data.get("amount")
            company_token = request.data.get("company_token")

            if card_uid is None or write_off_amount is None or company_token is None:
                return Response(data={"success": False, "message": "Error. Incorrect request body."}, status=400)

            # TODO: create global settings or just take current domain
            response = requests.get(f"http://localhost:8000/client_api/get_card_balance/{card_uid}")
            if response.status_code != 200:
                return Response(data={"success": False, "message": f"Error. Card UID is incorrect."}, status=404)

            card_current_balance = response.json()["balance"]
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

            card.balance = card.balance - Decimal(write_off_amount)
            company.balance = company.balance + Decimal(write_off_amount)

            with transaction.atomic():  # Save changes if transaction
                card.save()
                company.save()

            return Response(data={"success": True, "message": ""}, status=200)
        except Exception as ex:
            return Response(data={"success": False, "message": f"Error. {str(ex)}."}, status=500)


class CreateReceipt(APIView):  # TODO: Inner view ????
    def post(self, request: Request):
        card = Card.objects.first()
        company = Company.objects.first()
        receipt = Receipt()
        receipt.card = card
        receipt.company = company
        receipt.save()
        return Response(data={"success": True, "message": ""})
