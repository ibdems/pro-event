from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from django.views.generic import DetailView, ListView

from demande.forms import ServiceHotesseForms
from demande.models import Demande, Service
from demande.utils import create_user_from_anonymous_user
from event.forms import EventForms, TicketForms
from event.models import Category
from event.tasks import send_demande_accepted_email, send_demande_rejected_email


class AdminRequiredMixin(UserPassesTestMixin):
    """Mixin pour limiter l'accès aux administrateurs"""

    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser


class DemandeListView(LoginRequiredMixin, ListView):
    """Vue pour afficher la liste des demandes"""

    model = Demande
    template_name = "dashboard/demandes/list.html"
    context_object_name = "demandes"

    def get_queryset(self):
        user = self.request.user

        # Si l'utilisateur est un admin, afficher toutes les demandes
        # Sinon, afficher uniquement les demandes de l'utilisateur
        if user.is_staff or user.is_superuser:
            queryset = (
                Demande.objects.all()
                .select_related("event", "ticket", "anonymous_user", "service_hotesse", "user")
                .prefetch_related("service")
            )
        else:
            queryset = (
                Demande.objects.filter(user=user)
                .select_related("event", "ticket", "anonymous_user", "service_hotesse", "user")
                .prefetch_related("service")
            )

        # Appliquer les filtres
        service = self.request.GET.get("service")
        if service:
            queryset = queryset.filter(service__accronyme=service)

        status = self.request.GET.get("status")
        if status:
            if status == "1":
                queryset = queryset.filter(status="accepted")
            elif status == "0":
                queryset = queryset.filter(status="pending")
            elif status == "-1":  # Ajouter filtre pour les demandes rejetées
                queryset = queryset.filter(status="rejected")

        # Filtre par type d'utilisateur (seulement pour les admins)
        if user.is_staff or user.is_superuser:
            user_type = self.request.GET.get("user_type")
            if user_type == "anonymous":
                queryset = queryset.filter(anonymous_user__isnull=False)
            elif user_type == "registered":
                queryset = queryset.filter(user__isnull=False)

        # Recherche
        search = self.request.GET.get("search")
        if search:
            if user.is_staff or user.is_superuser:
                # Recherche plus large pour les admins
                queryset = queryset.filter(
                    Q(anonymous_user__first_name__icontains=search)
                    | Q(anonymous_user__last_name__icontains=search)
                    | Q(anonymous_user__email__icontains=search)
                    | Q(user__first_name__icontains=search)
                    | Q(user__last_name__icontains=search)
                    | Q(user__email__icontains=search)
                    | Q(event__title__icontains=search)
                )
            else:
                # Recherche limitée pour les organisateurs
                queryset = queryset.filter(Q(event__title__icontains=search))

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["services"] = Service.objects.all()
        return context


class DemandeDetailView(LoginRequiredMixin, DetailView):
    """Vue pour afficher les détails d'une demande"""

    model = Demande
    template_name = "dashboard/demandes/detail.html"
    context_object_name = "demande"
    pk_url_kwarg = "uid"

    def get_object(self, queryset=None):
        user = self.request.user
        demande = get_object_or_404(Demande, uid=self.kwargs.get(self.pk_url_kwarg))

        # Vérifier si l'utilisateur est autorisé à voir cette demande
        if not user.is_staff and not user.is_superuser and demande.user != user:
            raise Http404("Vous n'avez pas la permission de voir cette demande.")

        return demande

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        demande = self.get_object()
        context["services"] = demande.service.all()

        # Ajouter un numéro de demande pour l'affichage (au lieu de l'ID)
        context["numero_demande"] = f"{demande.pk:06d}"

        # Ajouter des variables d'état pour faciliter les conditions dans le template
        context["is_pending"] = demande.status == "pending"
        context["is_accepted"] = demande.status == "accepted"
        context["is_rejected"] = demande.status == "rejected"

        return context


class DemandeAcceptView(AdminRequiredMixin, LoginRequiredMixin, DetailView):
    """Vue pour accepter une demande (Admin seulement)"""

    model = Demande
    pk_url_kwarg = "uid"

    def get_object(self, queryset=None):
        return get_object_or_404(Demande, uid=self.kwargs.get(self.pk_url_kwarg))

    def post(self, request, *args, **kwargs):
        demande = self.get_object()

        # Vérifier si la demande a déjà été traitée
        if demande.status != "pending":
            if demande.status == "accepted":
                messages.warning(
                    request, "Cette demande a déjà été acceptée et ne peut pas être modifiée."
                )
            else:
                messages.warning(
                    request, "Cette demande a déjà été rejetée et ne peut pas être modifiée."
                )
            return redirect("dashboard:demande_detail", uid=demande.uid)

        password = None

        # Si c'est un utilisateur anonyme, créer un compte utilisateur
        if demande.anonymous_user and not demande.user:
            user, password = create_user_from_anonymous_user(demande.anonymous_user)
            demande.user = user

            # Associer l'utilisateur à l'événement si la demande en a un
            if demande.event:
                demande.event.user = user
                demande.event.save()
        elif demande.user and demande.event and not demande.event.user:
            # Si la demande a déjà un utilisateur mais l'événement n'en a pas
            demande.event.user = demande.user
            demande.event.save()

        # Marquer la demande comme acceptée
        demande.status = "accepted"
        demande.save()

        # Si la demande a un événement, l'activer
        if demande.event:
            demande.event.statut = True
            demande.event.save()

        # Envoyer l'email de confirmation
        send_demande_accepted_email.delay(str(demande.uid), password)

        messages.success(
            request,
            "La demande a été acceptée avec succès. Un email"
            " de confirmation a été envoyé au demandeur.",
        )
        return redirect("dashboard:demande_detail", uid=demande.uid)


class DemandeRejectView(AdminRequiredMixin, LoginRequiredMixin, DetailView):
    """Vue pour rejeter une demande (Admin seulement)"""

    model = Demande
    pk_url_kwarg = "uid"

    def get_object(self, queryset=None):
        return get_object_or_404(Demande, uid=self.kwargs.get(self.pk_url_kwarg))

    def post(self, request, *args, **kwargs):
        demande = self.get_object()

        # Vérifier si la demande a déjà été traitée
        if demande.status != "pending":
            if demande.status == "accepted":
                messages.warning(
                    request, "Cette demande a déjà été acceptée et ne peut pas être modifiée."
                )
            else:
                messages.warning(
                    request, "Cette demande a déjà été rejetée et ne peut pas être modifiée."
                )
            return redirect("dashboard:demande_detail", uid=demande.uid)

        # Marquer la demande comme rejetée
        demande.status = "rejected"
        demande.save()

        # Envoyer l'email de rejet
        send_demande_rejected_email.delay(str(demande.uid))

        messages.success(
            request,
            "La demande a été rejetée avec succès. Un email"
            " de notification a été envoyé au demandeur.",
        )
        return redirect("dashboard:demande_detail", uid=demande.uid)


class DemandeCreateView(LoginRequiredMixin, View):
    """Vue pour créer une demande"""

    def get(self, request):
        categories = Category.objects.all()
        services = Service.objects.all()
        context = {
            "categories": categories,
            "services": services,
            "service_hotesse_forms": ServiceHotesseForms(),
            "event_forms": EventForms(),
            "ticket_forms": TicketForms(),
            "active_page": "demande_create",
        }
        return render(request, "dashboard/demandes/create.html", context)

    def post(self, request):
        # Récupération des services sélectionnés
        selected_services_input = request.POST.get("selected_services", "")
        selected_services = selected_services_input.split(",") if selected_services_input else []

        forms_data = {
            "event": EventForms(request.POST, request.FILES),
            "ticket": TicketForms(request.POST),
            "hostess": ServiceHotesseForms(request.POST),
        }

        # Initialisation des instances
        instances = {"event": None, "ticket": None, "hostess": None}

        # Validation des formulaires en fonction des services sélectionnés
        is_valid = True

        # Validation des formulaires pour chaque service sélectionné
        if "event" in selected_services:
            if not forms_data["event"].is_valid():
                is_valid = False
            else:
                instances["event"] = forms_data["event"].save(commit=False)
                instances["event"].statut = False
                instances["event"].user = request.user

        if "ticket" in selected_services:
            if not forms_data["event"].is_valid() or not forms_data["ticket"].is_valid():
                is_valid = False
            else:
                instances["event"] = forms_data["event"].save(commit=False)
                instances["event"].statut = False
                instances["event"].user = request.user
                instances["ticket"] = forms_data["ticket"].save(commit=False)
                instances["ticket"].event = instances["event"]

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
                user=request.user,
            )

            # Ajout des services sélectionnés
            if selected_services:
                services = Service.objects.filter(accronyme__in=selected_services)
                demande.service.set(services)

            messages.success(
                request,
                "Votre demande a bien été effectuée. Il sera traité dans les plus brefs délais.",
            )
            return redirect("dashboard:demande_list")

        # En cas d'erreur, on retourne le formulaire avec les erreurs
        messages.error(
            request,
            "Une erreur est survenue lors de la création de votre demande. "
            "Veuillez vérifier les informations saisies.",
        )

        context = {
            "categories": Category.objects.all(),
            "services": Service.objects.all(),
            "service_hotesse_forms": forms_data["hostess"],
            "event_forms": forms_data["event"],
            "ticket_forms": forms_data["ticket"],
            "errors": {
                "event": forms_data["event"].errors,
                "ticket": forms_data["ticket"].errors,
                "hostess": forms_data["hostess"].errors,
            },
        }
        return render(request, "dashboard/demandes/create.html", context)
