from django.contrib import admin

from .models import *
# Register your models here.

# To see User table on admin site
admin.site.register(Chat)
admin.site.register(Message)