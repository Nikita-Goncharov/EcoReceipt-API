from django.urls import path
from . import views

urlpatterns = [
    path("get_card_balance/<str:card_uid>/", views.GetCardBalance.as_view()),
    # get_company_balance
    # get_user_cards
    # get_all_receipts
    # get_receipts_by_card
    # get_one_receipt
]
