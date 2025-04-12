from django import forms
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import TemplateView, UpdateView

from event.models import Event, Ticket


class UserProfileForm(forms.ModelForm):
    """Formulaire pour modifier le profil utilisateur"""

    first_name = forms.CharField(
        label="Prénom", required=False, widget=forms.TextInput(attrs={"class": "form-control"})
    )

    last_name = forms.CharField(
        label="Nom", required=False, widget=forms.TextInput(attrs={"class": "form-control"})
    )

    email = forms.EmailField(
        label="Email", required=True, widget=forms.EmailInput(attrs={"class": "form-control"})
    )

    contact = forms.CharField(
        label="Téléphone", required=False, widget=forms.TextInput(attrs={"class": "form-control"})
    )

    adresse = forms.CharField(
        label="Adresse", required=False, widget=forms.TextInput(attrs={"class": "form-control"})
    )

    class Meta:
        from users.models import User

        model = User
        fields = ["first_name", "last_name", "email", "contact", "adresse", "role"]
        widgets = {"role": forms.Select(attrs={"class": "form-control form-select"})}


class ProfileView(LoginRequiredMixin, TemplateView):
    """Vue pour afficher le profil de l'utilisateur connecté"""

    template_name = "dashboard/profile/view.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Récupérer les événements de l'utilisateur
        user_events = Event.objects.filter(user=user).order_by("-created_at")
        context["user_events"] = user_events
        context["user_events_count"] = user_events.count()

        # Récupérer les tickets vendus par l'utilisateur
        user_tickets = Ticket.objects.filter(event__user=user)
        context["user_tickets_count"] = user_tickets.count()

        # Calculer les revenus totaux
        total_revenue = sum(
            ticket.payement.amount
            for ticket in user_tickets
            if ticket.payement and ticket.payement.amount and ticket.payement.statut_payement
        )
        context["user_revenue"] = f"{total_revenue:,}".replace(",", " ") + " FCFA"

        # Activité récente (exemple simpliste)
        context["user_activities"] = [
            {
                "title": "Connexion",
                "description": "Vous vous êtes connecté à votre compte",
                "timestamp": user.last_login,
                "icon": "fas fa-sign-in-alt",
                "badge_class": "bg-success",
            }
        ]

        # Ajouter des activités basées sur les événements
        for event in user_events[:3]:  # Limiter aux 3 derniers événements
            context["user_activities"].append(
                {
                    "title": f"Événement créé: {event.title}",
                    "description": "Vous avez créé un nouvel événement",
                    "timestamp": event.created_at,
                    "icon": "fas fa-calendar-plus",
                    "badge_class": "bg-primary",
                }
            )

        # Trier les activités par date
        context["user_activities"].sort(
            key=lambda x: x["timestamp"] if x["timestamp"] else user.date_joined, reverse=True
        )

        return context


class ProfileEditView(LoginRequiredMixin, UpdateView):
    """Vue pour modifier le profil de l'utilisateur connecté"""

    form_class = UserProfileForm
    template_name = "dashboard/profile/edit.html"
    success_url = reverse_lazy("dashboard:profile")

    def get_object(self, queryset=None):
        return self.request.user

    def post(self, request, *args, **kwargs):
        # Vérifier si c'est une demande de changement de mot de passe
        if "password_change" in request.POST:
            form = PasswordChangeForm(request.user, request.POST)
            if form.is_valid():
                user = form.save()
                # Mettre à jour la session pour éviter la déconnexion
                update_session_auth_hash(request, user)
                messages.success(request, "Votre mot de passe a été mis à jour avec succès.")
                return redirect(self.success_url)
            else:
                messages.error(request, "Erreur dans le formulaire. Veuillez corriger les erreurs.")
                return render(
                    request, self.template_name, {"form": self.get_form(), "password_form": form}
                )

        # Vérifier si c'est une mise à jour de photo de profil
        elif "photo" in request.FILES:
            user = self.get_object()
            user.photo = request.FILES["photo"]
            user.save()
            messages.success(request, "Votre photo de profil a été mise à jour avec succès.")
            return redirect(self.success_url)

        # Sinon, c'est une mise à jour normale du profil
        return super().post(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Ajouter le formulaire de changement de mot de passe au contexte
        if "password_form" not in context:
            context["password_form"] = PasswordChangeForm(self.request.user)
        return context

    def form_valid(self, form):
        form.save()
        messages.success(self.request, "Votre profil a été mis à jour avec succès.")
        return redirect(self.success_url)
