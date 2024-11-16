from django.urls import path
from . import views
from . import auth_views

urlpatterns = [
    path("register_user/", auth_views.RegisterUser.as_view()),
    path("register_card/", auth_views.RegisterCard.as_view()),
    path("register_company/", auth_views.RegisterCompany.as_view()),
    path("login/", auth_views.LoginUser.as_view()),
    path("logout/", auth_views.LogoutUser.as_view()),
    path("get_user_info/", auth_views.GetUserInfo.as_view()),

    # get_card_balance - inner view
    path("increase_card_balance/", views.IncreaseCardBalance.as_view()),
    path("increase_company_balance/", views.IncreaseCompanyBalance.as_view()),

    # path("get_receipts_by_cards/", views.GetUserCardsReceipts.as_view()),
    path("get_user_transactions/", views.GetUserTransactions.as_view()),

    path("create_increase_balance_request/", views.CreateIncreaseBalanceRequest.as_view()),
    path("get_increase_balance_requests/", views.GetIncreaseBalanceRequests.as_view()),
    path("consider_increase_balance_request/", views.ConsiderIncreaseBalanceRequests.as_view()),

    path("get_cards/", views.GetUserCards.as_view())
    # TODO:
    # get_company_balance
    # get_user_cards
    # get_all_receipts
    # get_receipts_by_card
    # get_one_receipt
]
