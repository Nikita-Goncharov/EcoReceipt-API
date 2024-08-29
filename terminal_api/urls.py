from django.urls import path

from . import views

urlpatterns = [
	path("write_off_money/", views.WriteOffMoney.as_view()),
	path("create_receipt/", views.CreateReceipt.as_view())
]
