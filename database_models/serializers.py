from django.contrib.auth.models import User
from rest_framework import serializers

from .models import Card, Company, Transaction, Profile, Receipt


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email", "password"]
        extra_kwargs = {
            "password": {"write_only": True}
        }

    def save(self, *args, **kwargs):
        instance = super().save(*args, **kwargs)
        instance.set_password(self.validated_data["password"])
        instance.save()
        return instance


class CardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Card
        fields = ["_card_number", "_cvv", "_balance", "_card_uid", "owner"]


class ReceiptSerializer(serializers.ModelSerializer):
    class Meta:
        model = Receipt
        fields = ["img"]


class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = ["name", "_company_token", "_balance"]


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ["card", "company", "receipt", "card_balance_before", "card_balance_after", "company_balance_before", "company_balance_after", "created"]


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ["user"]