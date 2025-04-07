from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import TemplateView, UpdateView


class AdminRequiredMixin(UserPassesTestMixin):
    """Mixin pour limiter l'accès aux administrateurs"""

    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser


class EmailTemplateEditView(AdminRequiredMixin, LoginRequiredMixin, UpdateView):
    """Vue pour éditer les modèles d'email"""

    template_name = "dashboard/settings/email_template_edit.html"

    def get_object(self, queryset=None):
        # Cette méthode devrait être implémentée pour récupérer le modèle d'email approprié
        pass


class StatsView(AdminRequiredMixin, LoginRequiredMixin, TemplateView):
    """Vue pour afficher les statistiques"""

    template_name = "dashboard/stats/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Ajouter les statistiques au contexte
        return context


class ReportsView(AdminRequiredMixin, LoginRequiredMixin, TemplateView):
    """Vue pour afficher les rapports"""

    template_name = "dashboard/reports/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Ajouter les données de rapport au contexte
        return context
