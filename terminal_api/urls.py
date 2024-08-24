from django.urls import path

from . import views

urlpatterns = [
	path("get_user_balance/", views.get_user_balance),
 	path("writing_off_money/", views.writing_off_money),
	path("create_receipt", views.create_receipt)
]
