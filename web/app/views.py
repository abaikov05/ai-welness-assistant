from django.shortcuts import render, redirect

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
# Create your views here.

def home(request):
    return render(request, "app/home.html", {})

def chat(request):
    return render(request, "app/chat.html", {})

def login_user(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('chat')
        else:
            messages.error(request, ("Failed to log in"))
            return redirect('login_user')
    else:
        form = AuthenticationForm(request)
        return render(request, 'app/authenticate/login.html', {'form': form})

def register_user(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data['username']
            password = form.cleaned_data['password1']
            user = authenticate(username=username, password=password)
            login(request, user)
            messages.success(request, ("Registration seccesful"))
            return redirect('chat')
    else:
        form = UserCreationForm()
    return render(request, 'app/authenticate/register.html', {'form': form})

def logout_user(request):
    logout(request)
    messages.success(request, ("Logged out."))
    return redirect('home')