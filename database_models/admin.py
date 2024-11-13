from django.contrib import admin
from .models import Card, Receipt, Profile, Company, Transaction, Product, ServiceSetting, IncreaseBalanceRequest


@admin.register(Card)
class CardAdmin(admin.ModelAdmin):
    list_display = ("_card_number", "_cvv", "_balance", "_card_uid", "created", "updated")


@admin.register(Receipt)
class ReceiptAdmin(admin.ModelAdmin):
    list_display = ('img', "created", "updated")


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user__username", "cards_list", "created", "updated")

    def cards_list(self, obj):
        return ", ".join([card.card_number for card in obj.cards.all()])
        pass
    cards_list.short_description = "Cards"


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "cost", "company_owner", "created", "updated")


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', '_company_token', '_balance', "created", "updated")


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ("card", "company", "receipt", "card_balance_before", "card_balance_after", "company_balance_before", "company_balance_after", "created", "updated")


@admin.register(ServiceSetting)
class ServiceSettingAdmin(admin.ModelAdmin):
    list_display = ("name", "value_type", "value", "description", "created", "updated")


@admin.register(IncreaseBalanceRequest)
class IncreaseBalanceRequestAdmin(admin.ModelAdmin):
    list_display = ("requested_money", "card___card_number", "attached_message", "request_status", "created", "updated")
