from django.contrib import admin

from .models import *
# Register your models here.

# To see tables on admin site
admin.site.register(Chat)
admin.site.register(Message)
admin.site.register(User_settings)
admin.site.register(User_profile)
admin.site.register(User_emotional_journal)
admin.site.register(User_balance)
admin.site.register(Balance_transaction)