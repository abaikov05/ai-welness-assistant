from django.urls import path

from . import views

urlpatterns = [
    path ("", views.home, name="home"),
    path ("chat", views.chat, name="chat"),
    path ("balance", views.balance, name="balance"),

    path ("login_user", views.login_user, name="login_user"),
    path ("register_user", views.register_user, name="register_user"),
    path ("logout_user", views.logout_user, name="logout_user"),
    
    path ("get_user_balance", views.get_user_balance, name="get_user_balance"),
    path ("balance/top-up", views.top_up_balance, name="top_up_balance"),
]