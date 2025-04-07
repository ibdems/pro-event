from django.contrib import messages
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
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


class UserAddView(AdminRequiredMixin, LoginRequiredMixin, CreateView):
    """Vue pour ajouter un nouvel utilisateur"""

    model = User
    form_class = UserCreationForm
    template_name = "dashboard/users/add.html"
    success_url = reverse_lazy("dashboard:user_list")

    def form_valid(self, form):
        user = form.save()
        messages.success(self.request, f"L'utilisateur {user.username} a été créé avec succès.")
        return redirect(self.success_url)


class UserDetailView(AdminRequiredMixin, LoginRequiredMixin, DetailView):
    """Vue pour afficher les détails d'un utilisateur"""

    model = User
    template_name = "dashboard/users/detail.html"
    context_object_name = "user"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.get_object()
        context["events"] = Event.objects.filter(user=user)
        context["tickets"] = Ticket.objects.filter(event__user=user)
        return context


class UserEditView(AdminRequiredMixin, LoginRequiredMixin, UpdateView):
    """Vue pour modifier un utilisateur existant"""

    model = User
    form_class = UserChangeForm
    template_name = "dashboard/users/edit.html"
    success_url = reverse_lazy("dashboard:user_list")

    def form_valid(self, form):
        user = form.save()
        messages.success(
            self.request, f"L'utilisateur {user.username} a été mis à jour avec succès."
        )
        return redirect("dashboard:user_detail", pk=user.pk)


class UserDeleteView(AdminRequiredMixin, LoginRequiredMixin, DeleteView):
    """Vue pour supprimer un utilisateur"""

    model = User
    template_name = "dashboard/users/delete.html"
    success_url = reverse_lazy("dashboard:user_list")

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        username = self.object.username
        self.object.delete()
        messages.success(request, f"L'utilisateur {username} a été supprimé avec succès.")
        return redirect(self.success_url)
