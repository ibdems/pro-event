from django.contrib import messages
from django.contrib.auth.forms import UserChangeForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import TemplateView, UpdateView

from event.models import Event


class ProfileView(LoginRequiredMixin, TemplateView):
    """Vue pour afficher le profil de l'utilisateur connecté"""

    template_name = "dashboard/profile/view.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["user"] = self.request.user
        context["user_events"] = Event.objects.filter(user=self.request.user).order_by(
            "-created_at"
        )
        return context


class ProfileEditView(LoginRequiredMixin, UpdateView):
    """Vue pour modifier le profil de l'utilisateur connecté"""

    form_class = UserChangeForm
    template_name = "dashboard/profile/edit.html"
    success_url = reverse_lazy("dashboard:profile")

    def get_object(self, queryset=None):
        return self.request.user

    def form_valid(self, form):
        form.save()
        messages.success(self.request, "Votre profil a été mis à jour avec succès.")
        return redirect(self.success_url)
