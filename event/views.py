from django.shortcuts import render
from django.views.generic import ListView
from .models import Event

class HomeView(ListView):
    model = Event
    template_name = 'event/accueil.html'
