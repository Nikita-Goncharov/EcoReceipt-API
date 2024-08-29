from django.contrib import admin
from .models import Card, Receipt, Profile, Company


@admin.register(Card)
class CardAdmin(admin.ModelAdmin):
    list_display = ("_card_number", "_cvv", "_balance", "_card_uid")


@admin.register(Receipt)
class ReceiptAdmin(admin.ModelAdmin):
    list_display = ('created', 'card___card_number', 'company__name')


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user__username', )


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', '_company_token', 'balance')
