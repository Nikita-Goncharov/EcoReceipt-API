from django.contrib import admin
from .models import Card, Receipt, Profile, Company, Transaction


@admin.register(Card)
class CardAdmin(admin.ModelAdmin):
    list_display = ("_card_number", "_cvv", "_balance", "_card_uid")


@admin.register(Receipt)
class ReceiptAdmin(admin.ModelAdmin):
    list_display = ('img',)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user__username', )


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', '_company_token', '_balance')

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ("card", "company", "created", "receipt", "card_balance_before", "card_balance_after", "company_balance_before", "company_balance_after")