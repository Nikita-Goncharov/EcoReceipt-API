# Generated by Django 5.1 on 2024-10-22 17:41

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('database_models', '0013_card__pin_code_alter_transaction_card'),
    ]

    operations = [
        migrations.AlterField(
            model_name='card',
            name='owner',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='cards', to='database_models.profile'),
        ),
    ]
