from django.shortcuts import render, redirect

from django.contrib.auth import authenticate, login, logout
# from django.contrib.auth.forms import AuthenticationForm
from .forms import RegisterUserForm, LoginUserForm
from django.contrib import messages
from .models import Message, Chat, User_profile

from .assistant.responder import *
# Create your views here.

def home(request):
    return render(request, "app/home.html", {})

def chat(request):
    return render(request, "app/chat.html", {})

def send_message(request):
    user_id = request.user
    message = request.POST['message']
    if Chat.objects.check(user=user_id):
        chat = Chat.objects.get(user=user_id)
    else:
        chat = Chat(user=user_id)
        chat.save()
    db_message = Message(chat=chat, text=message)
    db_message.save()

    user_profile = User_profile(user=user_id)
    previous_message = Message.objects.filter(chat=chat).latest('text')

    # responder = Responder(user_profile, previous_message)
    # 
    # response = await responder.handle_user_message(message)

    return redirect('chat')

def login_user(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('chat')
        else:
            form = LoginUserForm(request)
            return render(request, 'app/authenticate/login.html', {'form': form, 'message': 'Wrong username or password!'})
    else:
        form = LoginUserForm(request)
        return render(request, 'app/authenticate/login.html', {'form': form, 'message': ''})

def register_user(request):
    if request.method == "POST":
        form = RegisterUserForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data['username']
            password = form.cleaned_data['password1']
            user = authenticate(username=username, password=password)
            login(request, user)
            messages.success(request, ("Registration seccesful"))
            return redirect('chat')
    else:
        form = RegisterUserForm()
    return render(request, 'app/authenticate/register.html', {'form': form})

def logout_user(request):
    logout(request)
    messages.success(request, ("Logged out."))
    return redirect('home')