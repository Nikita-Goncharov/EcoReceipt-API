# Generated by Django 5.1 on 2024-09-23 09:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('database_models', '0008_alter_company_building_alter_company_city_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='telegram_chat_id',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
    ]