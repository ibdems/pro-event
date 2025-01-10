from django.views.generic import CreateView, ListView, TemplateView

from .forms import ContactForm
from .models import Contact, Event


class HomeView(ListView):
    model = Event
    template_name = "event/accueil.html"
    context_object_name = "events"

    def get_queryset(self):
        qr = super().get_queryset()
        return qr.filter(statut=True).order_by("-created_at")[:3]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["active_page"] = "home"
        return context


class AboutView(TemplateView):
    template_name = "event/apropos.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["active_page"] = "about"
        return context


class EventView(ListView):
    model = Event
    template_name = "event/event.html"
    context_object_name = "events"
    paginate_by = 12

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["active_page"] = "event"
        return context


class ContactView(CreateView):
    template_name = "event/contact.html"
    model = Contact
    form_class = ContactForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["active_page"] = "contact"
        return context
