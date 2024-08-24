from django.contrib.auth.models import User
from django.db import models


class Profile(models.Model):
	balance = models.DecimalField(max_digits=10, decimal_places=2)
	user = models.OneToOneField(to=User, on_delete=models.CASCADE)


class Card(models.Model):
    card_number = models.CharField(max_length=16)
    cvv = models.CharField(max_length=3)
    owner = models.ForeignKey(to=Profile, on_delete=models.CASCADE)
    # foreign key to number of bank account


class Check(models.Model):
    pass
    # TODO


class Company(models.Model):
	name = models.CharField(max_length=100)
	company_token = models.CharField(max_length=150)
	balance = models.DecimalField(max_digits=15, decimal_places=2)