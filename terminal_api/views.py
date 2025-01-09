import logging
from decimal import Decimal
from multiprocessing import Process

from django.contrib.sites.shortcuts import get_current_site
from django.db import transaction as django_transaction
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.views import APIView

from telegram_bot.bot_send_receipt import run_async_in_process
from client_api.views import GetCardBalance
from database_models.models import Card, Company, Receipt, Transaction


class WriteOffMoney(APIView):
    @django_transaction.atomic
    def post(self, request: Request):
        try:
            card_uid = request.data.get("card_uid")
            write_off_amount = Decimal(request.data.get("amount", 0))  # TODO: check if write_off_amount is numeric
            company_token = request.data.get("company_token")
            logging.log(
                logging.INFO,
                f"Data from request - card_uid: {card_uid}, write_off_amount: {write_off_amount}, company_token: {company_token}",
            )

            if card_uid is None or write_off_amount is None or company_token is None:
                return Response(
                    data={
                        "success": False,
                        "message": "Error. Incorrect request body.",
                        "terminal_message": "Data is invalid",  # message for showing on terminal lcd (max length 16 symbols)
                    },
                    status=400,
                )

            response = GetCardBalance().get(request=request, card_uid=card_uid)
            if response.status_code != 200:
                return Response(
                    data={
                        "success": False,
                        "message": "Error. Card UID is incorrect.",
                        "terminal_message": "Card is invalid",
                    },
                    status=404,
                )

            card_current_balance = response.data["balance"]
            logging.log(logging.INFO, f"Current user card balance: {card_current_balance}")

            if Decimal(card_current_balance) < write_off_amount:  # Check if card balance bigger then write off sum
                return Response(
                    data={
                        "success": False,
                        "message": "Error. Card balance lower than write off sum.",
                        "terminal_message": "Balance is low",
                    },
                    status=400,
                )

            companies = Company.objects.filter(_company_token=company_token)
            if not companies.count():  # Check if company registered in system
                return Response(
                    data={
                        "success": False,
                        "message": "Error. There is no registered company with this token.",
                        "terminal_message": "Token is invalid",
                    },
                    status=404,
                )

            logging.log(logging.INFO, "Start of making payment transaction")
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

            card.balance = card.balance - write_off_amount
            company.balance = company.balance + write_off_amount

            card.save()
            company.save()

            transaction.card_balance_after = card.balance
            transaction.company_balance_after = company.balance
            transaction.save()
            logging.log(logging.INFO, "End of making payment transaction")

            receipt_path = transaction.receipt.get_receipt_img()
            logging.log(logging.INFO, f"Generated receipt path: {receipt_path}")

            # If user logged in, then send receipt to telegram bot
            tokens = Token.objects.filter(user=card.owner.user)
            logging.log(logging.INFO, f"Check if user logged in system by tokens: {tokens}")
            if tokens.count() != 0:
                logging.log(logging.INFO, "Making subprocess for async sending receipt image in telegram bot")
                request_site = get_current_site(request)
                logging.log(logging.INFO, f"Current site: {request_site.domain}")
                process = Process(
                    target=run_async_in_process,
                    args=(
                        f"http://{request_site.domain}/media/{receipt_path}",
                        card.owner.telegram_chat_id,
                        f"Card balance: {card.balance}",
                    ),
                )
                process.start()

            return Response(
                data={
                    "success": True,
                    "transaction_id": transaction.id,
                    "message": "",
                    "terminal_message": "Payment success",
                },
                status=200,
            )
        except Exception as ex:
            logging.log(logging.INFO, f"WriteOffMoney finished with unexpected error: {str(ex)}")
            return Response(
                data={"success": False, "message": f"Error. {str(ex)}.", "terminal_message": "Unexpected error"},
                status=500,
            )
