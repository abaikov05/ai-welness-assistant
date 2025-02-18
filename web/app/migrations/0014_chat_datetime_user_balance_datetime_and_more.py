# Generated by Django 4.2.5 on 2024-01-05 11:42

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0013_rename_balance_transactions_balance_transaction_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='chat',
            name='datetime',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AddField(
            model_name='user_balance',
            name='datetime',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AddField(
            model_name='user_profile',
            name='datetime',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AddField(
            model_name='user_settings',
            name='datetime',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AlterField(
            model_name='user_profile',
            name='content',
            field=models.TextField(default='[]', max_length=4000),
        ),
    ]
