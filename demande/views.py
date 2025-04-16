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
        context = {
            "categories": categories,
            "services": services,
            "anonymous_user_forms": AnonymousUserForms(),
            "service_hotesse_forms": ServiceHotesseForms(),
            "event_forms": EventForms(),
            "ticket_forms": TicketForms(),
        }
        return render(request, "event/demande.html", context)

    def post(self, request):
        print(request.POST)
        # Récupération des services sélectionnés
        selected_services_input = request.POST.get("selected_services", "")
        selected_services = selected_services_input.split(",") if selected_services_input else []

        forms_data = {
            "anonymous_user": AnonymousUserForms(request.POST),
            "event": EventForms(request.POST, request.FILES),
            "ticket": TicketForms(request.POST),
            "hostess": ServiceHotesseForms(request.POST),
        }

        # Initialisation des instances
        instances = {"event": None, "ticket": None, "hostess": None, "anonymous_user": None}

        # Validation des formulaires en fonction des services sélectionnés
        is_valid = True

        # Validation du formulaire utilisateur anonyme si non authentifié
        if not request.user.is_authenticated:
            if not forms_data["anonymous_user"].is_valid():
                is_valid = False
            else:
                instances["anonymous_user"] = forms_data["anonymous_user"].save(commit=False)

        # Validation des formulaires pour chaque service sélectionné
        if "event" in selected_services:
            if not forms_data["event"].is_valid():
                print(forms_data["event"].errors)
                is_valid = False
            else:
                instances["event"] = forms_data["event"].save(commit=False)
                instances["event"].statut = False
                if request.user.is_authenticated:
                    instances["event"].user = request.user

        if "ticket" in selected_services:
            if not forms_data["event"].is_valid() or not forms_data["ticket"].is_valid():
                print(f" {forms_data["event"].errors}, {forms_data["ticket"].errors}")
                is_valid = False
            else:
                instances["event"] = forms_data["event"].save(commit=False)
                instances["event"].statut = False
                # Associer l'utilisateur à l'événement si authentifié
                if request.user.is_authenticated:
                    instances["event"].user = request.user
                instances["ticket"] = forms_data["ticket"].save(commit=False)
                instances["ticket"].event = instances["event"]
                print(instances["ticket"])

        if "hostess" in selected_services:
            if not forms_data["hostess"].is_valid():
                is_valid = False
            else:
                instances["hostess"] = forms_data["hostess"].save(commit=False)

        # Si tous les formulaires requis sont valides, on sauvegarde les instances
        if is_valid and any(instances.values()):
            # Sauvegarde des instances
            for instance in instances.values():
                if instance:
                    instance.save()

            # Liaison du ticket à l'événement si nécessaire
            if instances["ticket"] and instances["event"]:
                instances["ticket"].event = instances["event"]
                instances["ticket"].save()

            # Création de la demande
            demande = Demande.objects.create(
                event=instances["event"],
                ticket=instances["ticket"],
                service_hotesse=instances["hostess"],
                anonymous_user=instances["anonymous_user"],
                user=request.user if request.user.is_authenticated else None,
            )

            # Ajout des services sélectionnés
            if selected_services:
                services = Service.objects.filter(accronyme__in=selected_services)
                demande.service.set(services)

            messages.success(
                request,
                "Votre demande a bien été effectuée. Vous recevrez un email pour "
                "la suite de notre accord. Merci pour votre confiance.",
            )
            return redirect("demande")

        # En cas d'erreur, on retourne le formulaire avec les erreurs
        messages.error(
            request,
            "Une erreur est survenue lors de la création de votre demande. "
            "Veuillez vérifier les informations saisies.",
        )

        context = {
            "categories": Category.objects.all(),
            "services": Service.objects.all(),
            "anonymous_user_forms": forms_data["anonymous_user"],
            "service_hotesse_forms": forms_data["hostess"],
            "event_forms": forms_data["event"],
            "ticket_forms": forms_data["ticket"],
            "errors": {
                "event": forms_data["event"].errors,
                "ticket": forms_data["ticket"].errors,
                "hostess": forms_data["hostess"].errors,
                "anonymous_user": forms_data["anonymous_user"].errors,
            },
        }
        return render(request, "event/demande.html", context)
