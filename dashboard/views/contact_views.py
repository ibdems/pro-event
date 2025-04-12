from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import ListView, View

from event.models import Contact
from users.models import User


class AdminRequiredMixin(UserPassesTestMixin):
    """Mixin pour limiter l'accès aux administrateurs"""

    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser


class BaseView(AdminRequiredMixin, LoginRequiredMixin, View):
    """Vue de base pour les vues de l'administration"""

    pass


class ContactListView(BaseView, ListView):
    """Vue pour afficher la liste des contacts"""

    model = Contact
    template_name = "dashboard/contacts/list.html"
    context_object_name = "contacts"

    def get_queryset(self):
        queryset = Contact.objects.all().order_by("-created_at")

        # Recherche
        search = self.request.GET.get("search")
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search)
                | Q(email__icontains=search)
                | Q(subject__icontains=search)
                | Q(message__icontains=search)
            )

        # Filtrage par date
        date_from = self.request.GET.get("date_from")
        if date_from:
            queryset = queryset.filter(created_at__date__gte=date_from)

        date_to = self.request.GET.get("date_to")
        if date_to:
            queryset = queryset.filter(created_at__date__lte=date_to)

        return queryset


class ContactDetailView(BaseView):
    template_name = "dashboard/contacts/detail.html"

    def get(self, request, id):
        contact = get_object_or_404(Contact, id=id)

        # Marquer le message comme lu s'il ne l'est pas déjà
        if not contact.is_read:
            contact.is_read = True
            contact.save()

        # Vérifier si cet email correspond à un utilisateur enregistré
        user_info = None
        try:
            user_info = User.objects.get(email=contact.email)
        except User.DoesNotExist:
            pass

        context = {
            "contact": contact,
            "user_info": user_info,
        }

        return render(request, self.template_name, context)


class ContactDeleteView(BaseView):
    """
    Vue pour supprimer un contact
    """

    def post(self, request, id):
        contact = get_object_or_404(Contact, id=id)
        contact.delete()
        messages.success(request, "Contact supprimé avec succès")
        return redirect("dashboard:contact_list")


class ContactBulkDeleteView(BaseView):
    """
    Vue pour supprimer plusieurs contacts en masse
    """

    def post(self, request):
        contact_ids = request.POST.get("contact_ids", "")
        if contact_ids:
            ids = [int(id) for id in contact_ids.split(",")]
            Contact.objects.filter(id__in=ids).delete()
            messages.success(request, f"{len(ids)} contacts supprimés avec succès")
        else:
            messages.error(request, "Aucun contact sélectionné")

        return redirect("dashboard:contact_list")


class ContactMarkReadView(BaseView):
    """
    Vue pour marquer un contact comme lu
    """

    def post(self, request, id):
        contact = get_object_or_404(Contact, id=id)
        contact.is_read = True
        contact.save()

        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"status": "success", "message": "Contact marqué comme lu"})
        else:
            return redirect("dashboard:contact_list")
