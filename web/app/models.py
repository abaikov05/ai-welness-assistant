from django.db import models
from django.conf import settings
from django.utils import timezone
# Create your models here.

class Chat(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    datetime = models.DateTimeField(default=timezone.now)

class Message(models.Model):
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE)
    time = models.DateTimeField(default=timezone.now)
    text = models.TextField(max_length=2500)
    is_bot = models.BooleanField(default=False)

class User_profile(models.Model):
    content = models.TextField(max_length=4000, default='[]')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    datetime = models.DateTimeField(default=timezone.now)

class User_settings(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    
    responder_personality = models.TextField(max_length=2500, default="Caring and helpful assistant.")
    responder_gpt_model = models.TextField(default='gpt-3.5-turbo')
    messages_for_input_extraction = models.PositiveSmallIntegerField(default=3)

    profiler_gpt_model = models.TextField(default='gpt-3.5-turbo')
    messages_till_profile_update = models.PositiveSmallIntegerField(default=5)
    messages_for_profile_update = models.PositiveSmallIntegerField(default=5)
    
    journal_gpt_model = models.TextField(default='gpt-3.5-turbo')
    messages_till_journal_update = models.PositiveSmallIntegerField(default=5)
    messages_for_journal_update = models.PositiveSmallIntegerField(default=5)

    datetime = models.DateTimeField(default=timezone.now)

class User_emotional_journal(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    journal = models.TextField(max_length=3000, default="{}")
    updates_count = models.PositiveSmallIntegerField(default=0)
    date = models.DateField(default=timezone.now)

class User_balance(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    balance = models.DecimalField(default=0, max_digits=7, decimal_places=4)
    datetime = models.DateTimeField(default=timezone.now)

class Balance_transaction(models.Model):
    balance = models.ForeignKey(User_balance, on_delete=models.CASCADE)
    type = models.TextField(max_length=100)
    amount = models.DecimalField(default=0, max_digits=7, decimal_places=4)
    datetime = models.DateTimeField(default=timezone.now)