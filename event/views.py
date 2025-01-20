from django.views.generic import CreateView, DetailView, ListView, TemplateView
from django_filters.views import FilterView

from .filter import EventFilter
from .forms import ContactForm, EventForms
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


class EventView(FilterView, ListView):
    model = Event
    template_name = "event/event.html"
    context_object_name = "events"
    paginate_by = 12
    filterset_class = EventFilter

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["active_page"] = "event"
        return context

    def get_ordering(self):
        order = super().get_ordering()
        return order or "-created_at"


class DetailEventView(DetailView):
    pk_url_kwarg = "uid"
    model = Event
    context_object_name = "event"
    template_name = "event/event_detail.html"

    def get_object(self, queryset=...):
        return (
            Event.objects.select_related("category", "user")
            .prefetch_related("partner")
            .get(uid=self.kwargs.get("uid"))
        )


class ContactView(CreateView):
    template_name = "event/contact.html"
    model = Contact
    form_class = ContactForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["active_page"] = "contact"
        return context


class EventAddView(CreateView):
    template_name = "event/event_add.html"
    model = Event
    form_class = EventForms
    success_url = "/event/"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["active_page"] = "event"
        return context

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)
