# Generated by Django 5.1 on 2024-09-14 19:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('database_models', '0003_alter_card__card_uid'),
    ]

    operations = [
        migrations.AddField(
            model_name='company',
            name='building',
            field=models.CharField(blank=True, max_length=10, null=True, unique=True),
        ),
        migrations.AddField(
            model_name='company',
            name='city',
            field=models.CharField(blank=True, max_length=40, null=True, unique=True),
        ),
        migrations.AddField(
            model_name='company',
            name='country',
            field=models.CharField(blank=True, max_length=40, null=True, unique=True),
        ),
        migrations.AddField(
            model_name='company',
            name='hotline_phone',
            field=models.CharField(blank=True, max_length=20, null=True, unique=True),
        ),
        migrations.AddField(
            model_name='company',
            name='street',
            field=models.CharField(blank=True, max_length=40, null=True, unique=True),
        ),
    ]