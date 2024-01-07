from decimal import Decimal

from django.shortcuts import render, redirect

from django.contrib.auth import authenticate, login, logout

from .forms import RegisterUserForm, LoginUserForm
from django.contrib import messages
from django.http import JsonResponse

from .models import Chat, User_profile, User_balance, User_settings

# Create your views here.

def home(request):
    return render(request, "app/home.html", {})

def chat(request):
    
    if request.user.is_authenticated:
        return render(request, "app/chat.html", {})
    else:
        return redirect('login_user')
    
def balance(request):
    
    if request.user.is_authenticated:
        return render(request, "app/balance.html", {})
    else:
        return redirect('login_user')

# Function to top up balance. ! ONLY FOR DEMONSTRATION PURPOSE !
def top_up_balance(request):
    user = request.user

    if user.is_authenticated:
        if request.method == 'POST':

            amount = Decimal(request.POST.get('amount', 0.00))

            balance = User_balance.objects.get(user = user)
            
            decimal_balance = Decimal(balance.balance)
            balance.balance = (decimal_balance + amount).quantize(Decimal('0.0001'), rounding='ROUND_FLOOR')
            balance.save()
            
            return redirect('chat')

    return redirect('home')

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

            user_profile = User_profile.objects.create(user=user)
            user_profile.save()
            user_balance = User_balance.objects.create(user=user)
            user_balance.save()
            user_settings = User_settings.objects.create(user=user)
            user_settings.save()
            user_chat = Chat.objects.create(user=user)
            user_chat.save()

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

def get_user_balance(request):

    user = request.user
    if user.is_authenticated:
        user_balance = User_balance.objects.get(user=user)
        return JsonResponse({'user_balance': user_balance.balance})
    else:
        return JsonResponse({'user_balance': None})
