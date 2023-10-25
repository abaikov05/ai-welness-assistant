from django.db import models
from django.conf import settings
from django.utils import timezone
# Create your models here.

class Chat(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

class Message(models.Model):
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE)
    time = models.DateTimeField(default=timezone.now)
    text = models.TextField(max_length=500)

class User_profile(models.Model):
    content = models.TextField(max_length=500)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
