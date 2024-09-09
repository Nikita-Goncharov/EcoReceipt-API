from django.urls import path
from . import views

urlpatterns = [
    path("register_user/", views.RegisterUser.as_view()),
    path("login/", views.LoginUser.as_view()),
    path("logout/", views.LogoutUser.as_view()),
    path("register_card/", views.RegisterCard.as_view()),
    # login_user
    # logout_user
    path("get_card_balance/<str:card_uid>/", views.GetCardBalance.as_view()),
    # get_company_balance
    # get_user_cards
    # get_all_receipts
    # get_receipts_by_card
    # get_one_receipt
]
