from django.contrib import messages
from django.shortcuts import redirect, render
from django.views import View

from demande.forms import AnonymousUserForms, ServiceHotesseForms
from demande.models import Demande, Service
from event.forms import EventForms, TicketForms
from event.models import Category


class DemandeView(View):
    def get(self, request):
        categories = Category.objects.all()
        services = Service.objects.all()
        anonymous_user_forms = AnonymousUserForms()
        service_hotesse_forms = ServiceHotesseForms()
        event_forms = EventForms()
        ticket_forms = TicketForms()
        context = {
            "categories": categories,
            "services": services,
            "anonymous_user_forms": anonymous_user_forms,
            "service_hotesse_forms": service_hotesse_forms,
            "event_forms": event_forms,
            "ticket_forms": ticket_forms,
        }
        return render(request, "event/demande.html", context)

    def post(self, request):
        selected_services = request.POST.getlist("selected_services")
        anonymous_user_form = AnonymousUserForms(request.POST)
        service_hotesse_form = ServiceHotesseForms(request.POST)
        ticket_info_form = TicketForms(request.POST)
        event_form = EventForms(request.POST)

        # Initialisation des instances à None
        event_instance = None
        ticket_instance = None
        hostess_instance = None
        anonymous_user_instance = None

        # Création des instances selon le choix des services
        if "event" in selected_services and event_form.is_valid():
            event_instance = event_form.save()

        if "ticket" in selected_services and event_form.is_valid() and ticket_info_form.is_valid():
            event_instance = event_form.save()
            ticket_instance = ticket_info_form.save(commit=False)
            ticket_instance.event = event_instance
            ticket_instance.save()

        if "hostess" in selected_services and service_hotesse_form.is_valid():
            hostess_instance = service_hotesse_form.save()

        if not request.user.is_authenticated and anonymous_user_form.is_valid():
            anonymous_user_instance = anonymous_user_form.save()

        if event_instance or ticket_instance or hostess_instance or anonymous_user_instance:
            demande_instance = Demande.objects.create(
                event=event_instance,
                ticket=ticket_instance,
                service_hotesse=hostess_instance,
                anonymous_user=anonymous_user_instance,
                user=request.user if request.user.is_authenticated else None,
            )
            if selected_services:
                services = Service.objects.filter(accronyme__in=selected_services)
                demande_instance.service.set(services)
            messages.success(
                request,
                "Votre demandé à bien été effectuer. Vous recevrez un mail pour "
                "la suite de notre accord. Merci pour la confiance.",
            )
            return redirect("demande")

        # Si le formulaire n'est pas valide, on recharge le formulaire avec les erreurs
        categories = Category.objects.all()
        services = Service.objects.all()
        context = {
            "categories": categories,
            "services": services,
            "anonymous_user_forms": anonymous_user_form,
            "service_hotesse_forms": service_hotesse_form,
            "event_forms": event_form,
            "ticket_forms": ticket_info_form,
            "errors": {
                "event": event_form.errors,
                "ticket": ticket_info_form.errors,
                "hostess": service_hotesse_form.errors,
                "anonymous_user": anonymous_user_form.errors,
            },
        }
        return render(request, "event/demande.html", context)
