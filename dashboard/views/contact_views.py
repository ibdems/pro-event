from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import DetailView, ListView, View

from event.models import Contact


class AdminRequiredMixin(UserPassesTestMixin):
    """Mixin pour limiter l'accès aux administrateurs"""

    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser


class ContactListView(LoginRequiredMixin, ListView):
    """Vue pour afficher la liste des contacts"""

    model = Contact
    template_name = "dashboard/contacts/list.html"
    context_object_name = "contacts"

    def get_queryset(self):
        return Contact.objects.all().order_by("-created_at")


class ContactDetailView(LoginRequiredMixin, DetailView):
    """Vue pour afficher les détails d'un contact"""

    model = Contact
    template_name = "dashboard/contacts/detail.html"
    context_object_name = "contact"

    def get_object(self, queryset=None):
        contact = get_object_or_404(Contact, pk=self.kwargs.get("pk"))

        # Marquer comme lu si ce n'est pas déjà fait
        if not contact.is_read:
            contact.is_read = True
            contact.save()

        return contact


class ContactMarkReadView(LoginRequiredMixin, View):
    """Vue pour marquer un contact comme lu"""

    def post(self, request, pk):
        contact = get_object_or_404(Contact, pk=pk)
        contact.is_read = True
        contact.save()

        messages.success(request, "Le message a été marqué comme lu.")
        return redirect("dashboard:contact_list")
