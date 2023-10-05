from django.shortcuts import render

# Create your views here.

def home(response):
    return render(response, "app/home.html")
