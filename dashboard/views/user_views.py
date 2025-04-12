from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Q
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from event.models import Event, Ticket
from users.forms import AdminUserChangeForm, AdminUserCreationForm
from users.models import User


class AdminRequiredMixin(UserPassesTestMixin):
    """Mixin pour limiter l'accès aux administrateurs"""

    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser


class UserListView(AdminRequiredMixin, LoginRequiredMixin, ListView):
    """Vue pour afficher la liste des utilisateurs"""

    model = User
    template_name = "dashboard/users/list.html"
    context_object_name = "users"

    def get_queryset(self):
        queryset = User.objects.all().order_by("-date_joined")

        # Filtrer par email
        email = self.request.GET.get("email")
        if email:
            queryset = queryset.filter(email__icontains=email)

        # Filtrer par rôle
        role = self.request.GET.get("role")
        if role == "admin":
            queryset = queryset.filter(is_superuser=True)
        elif role == "organizer":
            queryset = queryset.filter(is_staff=True, is_superuser=False)
        elif role == "user":
            queryset = queryset.filter(is_staff=False, is_superuser=False)

        # Filtrer par statut
        is_active = self.request.GET.get("is_active")
        if is_active == "1":
            queryset = queryset.filter(is_active=True)
        elif is_active == "0":
            queryset = queryset.filter(is_active=False)

        # Filtrer par date d'inscription
        date_joined_after = self.request.GET.get("date_joined_after")
        if date_joined_after:
            queryset = queryset.filter(date_joined__date__gte=date_joined_after)

        # Filtrer par dernière connexion
        last_login_after = self.request.GET.get("last_login_after")
        if last_login_after:
            queryset = queryset.filter(
                Q(last_login__date__gte=last_login_after) | Q(last_login__isnull=True)
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Ajouter des filtres aux contexte pour maintenir les valeurs sélectionnées
        context["filters"] = {
            "email": self.request.GET.get("email", ""),
            "role": self.request.GET.get("role", ""),
            "is_active": self.request.GET.get("is_active", ""),
            "date_joined_after": self.request.GET.get("date_joined_after", ""),
            "last_login_after": self.request.GET.get("last_login_after", ""),
        }
        return context


class UserAddView(AdminRequiredMixin, LoginRequiredMixin, CreateView):
    """Vue pour ajouter un nouvel utilisateur"""

    model = User
    form_class = AdminUserCreationForm
    template_name = "dashboard/users/add.html"
    success_url = reverse_lazy("dashboard:user_list")

    def form_valid(self, form):
        user = form.save()

        # Si un mot de passe a été généré, l'afficher dans le message
        if hasattr(user, "generated_password"):
            messages.success(
                self.request,
                f"L'utilisateur {user.email} a été créé avec succès. "
                f"Mot de passe généré: {user.generated_password}",
            )
        else:
            messages.success(self.request, f"L'utilisateur {user.email} a été créé avec succès.")

        return redirect(self.success_url)


class UserDetailView(AdminRequiredMixin, LoginRequiredMixin, DetailView):
    """Vue pour afficher les détails d'un utilisateur"""

    model = User
    template_name = "dashboard/users/detail.html"
    context_object_name = "user"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.get_object()

        # Récupérer les événements de l'utilisateur
        context["events"] = Event.objects.filter(user=user)

        # Récupérer les tickets liés aux événements de l'utilisateur
        context["tickets"] = Ticket.objects.filter(event__user=user)

        # Récupérer les demandes si le modèle existe
        try:
            from demande.models import Demande

            context["demandes"] = Demande.objects.filter(user=user)
        except (ImportError, ModuleNotFoundError):
            context["demandes"] = []

        return context


class UserEditView(AdminRequiredMixin, LoginRequiredMixin, UpdateView):
    """Vue pour modifier un utilisateur existant"""

    model = User
    form_class = AdminUserChangeForm
    template_name = "dashboard/users/edit.html"
    success_url = reverse_lazy("dashboard:user_list")

    def form_valid(self, form):
        user = form.save()

        # Si un mot de passe a été réinitialisé, l'afficher dans le message
        if hasattr(user, "generated_password"):
            messages.success(
                self.request,
                f"L'utilisateur {user.email} a été mis à jour avec succès. "
                f"Nouveau mot de passe généré: {user.generated_password}",
            )
        else:
            messages.success(
                self.request, f"L'utilisateur {user.email} a été mis à jour avec succès."
            )

        return redirect("dashboard:user_detail", pk=user.pk)


class UserDeleteView(AdminRequiredMixin, LoginRequiredMixin, DeleteView):
    """Vue pour supprimer un utilisateur"""

    model = User
    template_name = "dashboard/users/delete.html"
    success_url = reverse_lazy("dashboard:user_list")

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        email = self.object.email
        self.object.delete()
        messages.success(request, f"L'utilisateur {email} a été supprimé avec succès.")
        return redirect(self.success_url)


class UserActivateView(AdminRequiredMixin, LoginRequiredMixin, DetailView):
    """Vue pour activer un utilisateur"""

    model = User

    def post(self, request, *args, **kwargs):
        user = self.get_object()
        user.is_active = True
        user.save()
        messages.success(request, f"L'utilisateur {user.email} a été activé avec succès.")
        return redirect("dashboard:user_list")


class UserDeactivateView(AdminRequiredMixin, LoginRequiredMixin, DetailView):
    """Vue pour désactiver un utilisateur"""

    model = User

    def post(self, request, *args, **kwargs):
        user = self.get_object()
        user.is_active = False
        user.save()
        messages.success(request, f"L'utilisateur {user.email} a été désactivé avec succès.")
        return redirect("dashboard:user_list")
