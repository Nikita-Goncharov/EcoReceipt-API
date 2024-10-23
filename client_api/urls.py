from django.urls import path
from . import views

urlpatterns = [
    path("register_user/", views.RegisterUser.as_view()),
    path("register_card/", views.RegisterCard.as_view()),
    path("register_company/", views.RegisterCompany.as_view()),
    path("login/", views.LoginUser.as_view()),
    path("logout/", views.LogoutUser.as_view()),

    # get_card_balance - inner view
    path("increase_card_balance/", views.IncreaseCardBalance.as_view()),
    path("increase_company_balance/", views.IncreaseCompanyBalance.as_view()),

    # path("get_receipts_by_cards/", views.GetUserCardsReceipts.as_view()),
    path("get_user_transactions/", views.GetUserTransactions.as_view()),

    # path("get_cards/", views.GetUserCards.as_view())
    # TODO:
    # get_company_balance
    # get_user_cards
    # get_all_receipts
    # get_receipts_by_card
    # get_one_receipt
]
