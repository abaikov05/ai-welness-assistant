# Generated by Django 4.2.5 on 2023-12-26 19:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0007_user_settings_messages_till_journal_update_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='user_settings',
            old_name='gpt_model',
            new_name='journal_gpt_model',
        ),
        migrations.AddField(
            model_name='user_settings',
            name='profiler_gpt_model',
            field=models.TextField(default='gpt-3.5-turbo'),
        ),
        migrations.AddField(
            model_name='user_settings',
            name='responder_gpt_model',
            field=models.TextField(default='gpt-3.5-turbo'),
        ),
    ]
