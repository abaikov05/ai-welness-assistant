from django.contrib import admin

from .models import User
# Register your models here.

# To see User table on admin site
admin.site.register(User)