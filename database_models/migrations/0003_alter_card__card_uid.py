# Generated by Django 5.1 on 2024-09-12 20:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('database_models', '0002_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='card',
            name='_card_uid',
            field=models.CharField(blank=True, max_length=8, null=True, unique=True),
        ),
    ]
