from decimal import Decimal

from django.shortcuts import render, redirect

from django.contrib.auth import authenticate, login, logout

from .forms import RegisterUserForm, LoginUserForm
from django.contrib import messages
from django.http import JsonResponse

from .models import Chat, User_profile, User_balance, User_settings, Balance_transaction, Message

from .utils import Encryption
from textwrap import dedent
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
            try:
                
                amount = Decimal(request.POST.get('amount', 0.00))

                balance = User_balance.objects.get(user = user)
                
                decimal_balance = Decimal(balance.balance)
                balance.balance = (decimal_balance + amount).quantize(Decimal('0.0001'), rounding='ROUND_FLOOR')
                balance.save()
                
                new_transaction = Balance_transaction(type = 'Top up', balance = balance, amount = amount)
                new_transaction.save()
                
                return redirect('chat')
            except Exception as e:
                print("Exeption during toping up balance: ", e)
                return redirect('home')

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

            encryption = Encryption()
            user_profile = User_profile.objects.create(user=user, content=encryption.encrypt('[]'))
            user_profile.save()
            user_balance = User_balance.objects.create(user=user)
            user_balance.save()
            user_settings = User_settings.objects.create(user=user)
            user_settings.save()
            user_chat = Chat.objects.create(user=user)
            user_chat.save()
            
            welcome = dedent("""\
                Welcome to your Wellbeing Assistant! 🌟
                
                You can adjust the assistant's module settings in the left panel (or above if you're using a phone).
                If you'd like to explore the tools available, simply send me a message, and I'll guide you through everything I can do to support your health and wellbeing. 😊
                
                Please note that while I strive to provide accurate and helpful information, as an AI, I can occasionally make mistakes. Always double-check critical advice or recommendations.
                
                Let's get started! 💬""")
            welcome_message = Message.objects.create(chat=user_chat, is_bot=True, text=encryption.encrypt(welcome))
            welcome_message.save()

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