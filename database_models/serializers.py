from django.contrib.auth.models import User
from rest_framework import serializers

from .models import Card, Company, Transaction, Profile, Receipt, Product


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


class ProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = Profile
        fields = ["user", "telegram_chat_id", "created", "updated"]
        extra_kwargs = {
            "telegram_chat_id": {"required": False, "default": ""},
            "created": {"read_only": True},
            "updated": {"read_only": True}
        }


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ["name", "description", "cost", "company_owner", "created", "updated"]
        extra_kwargs = {
            "name": {"required": True},
            "description": {"required": True},

            "created": {"read_only": True},
            "updated": {"read_only": True}
        }


class ReceiptSerializer(serializers.ModelSerializer):
    class Meta:
        model = Receipt
        fields = ["img", "created", "updated"]
        extra_kwargs = {
            "created": {"read_only": True},
            "updated": {"read_only": True}
        }


class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = ["name", "_balance", "hotline_phone", "country", "city", "street", "building", "created", "updated"]
        extra_kwargs = {
            "name": {"required": True},
            "hotline_phone": {"required": True},
            "country": {"required": True},
            "city": {"required": True},
            "street": {"required": True},
            "building": {"required": True},

            "_balance": {"read_only": True},
            "created": {"read_only": True},
            "updated": {"read_only": True}
        }


class TransactionSerializer(serializers.ModelSerializer):
    receipt = ReceiptSerializer()
    company = CompanySerializer()

    class Meta:
        model = Transaction
        fields = ["card", "company", "receipt", "card_balance_before", "card_balance_after", "company_balance_before", "company_balance_after", "created", "updated"]
        extra_kwargs = {
            "created": {"read_only": True},
            "updated": {"read_only": True}
        }


class CardSerializer(serializers.ModelSerializer):
    transactions = TransactionSerializer(many=True)
    owner = ProfileSerializer()

    class Meta:
        model = Card
        fields = ["_card_number", "_cvv", "_balance", "_card_uid", "owner", "transactions", "created", "updated"]
        extra_kwargs = {
            "_card_number": {"read_only": True},
            "_cvv": {"read_only": True},
            "_balance": {"read_only": True},
            "transactions": {"read_only": True},
            "created": {"read_only": True},
            "updated": {"read_only": True}
        }
