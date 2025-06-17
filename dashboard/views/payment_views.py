from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q, Sum
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.generic import DetailView, ListView

from event.models import Payement
from event.tasks import send_ticket_by_email


class PaymentListView(LoginRequiredMixin, ListView):
    model = Payement
    template_name = "dashboard/payments/list.html"
    context_object_name = "payments"
    paginate_by = 10

    def get_queryset(self):
        queryset = Payement.objects.select_related("event").order_by("-created_at")

        # Filtrage par statut
        status = self.request.GET.get("status")
        if status:
            queryset = queryset.filter(statut_payement=status)

        # Filtrage par méthode de paiement
        payment_method = self.request.GET.get("payment_method")
        if payment_method:
            queryset = queryset.filter(payment_method=payment_method)

        # Recherche
        search = self.request.GET.get("search")
        if search:
            queryset = queryset.filter(
                Q(reference_payement__icontains=search)
                | Q(nom_complet__icontains=search)
                | Q(email_reception__icontains=search)
                | Q(telephone_reception__icontains=search)
                | Q(event__title__icontains=search)
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        payments = self.get_queryset()

        # Statistiques générales
        context["total_amount"] = (
            payments.filter(statut_payement="valide").aggregate(Sum("amount"))["amount__sum"] or 0
        )
        context["total_payments"] = payments.count()

        # Statistiques par statut
        context["validated_payments"] = payments.filter(statut_payement="valide").count()
        context["pending_payments"] = payments.filter(statut_payement="en_attente").count()
        context["failed_payments"] = payments.filter(statut_payement="echec").count()

        # Montant total par statut
        context["validated_amount"] = (
            payments.filter(statut_payement="valide").aggregate(total=Sum("amount"))["total"] or 0
        )
        context["pending_amount"] = (
            payments.filter(statut_payement="en_attente").aggregate(total=Sum("amount"))["total"]
            or 0
        )

        # Statistiques par méthode de paiement
        payment_methods = payments.values("payment_method").annotate(
            count=Count("id"), total=Sum("amount")
        )
        context["payment_methods_stats"] = payment_methods

        # Définir les choix de statut manuellement
        context["status_choices"] = {
            "en_attente": "En attente",
            "valide": "Validé",
            "echec": "Échoué",
        }

        # Récupérer les choix de méthode de paiement depuis le modèle
        context["payment_method_choices"] = dict(Payement._meta.get_field("payment_method").choices)
        return context


class PaymentDetailView(LoginRequiredMixin, DetailView):
    model = Payement
    template_name = "dashboard/payments/detail.html"
    context_object_name = "payment"
    pk_url_kwarg = "id"

    def get_object(self, queryset=None):
        return get_object_or_404(Payement.objects.select_related("event"), id=self.kwargs.get("id"))

    def post(self, request, *args, **kwargs):
        payment = self.get_object()
        if payment.email_reception:
            # Envoyer le reçu par email
            send_ticket_by_email.delay(payment.id)
            messages.success(request, "Le reçu a été envoyé avec succès.")
        else:
            messages.warning(
                request, "Impossible d'envoyer le reçu : aucun email associé à ce paiement."
            )
        return HttpResponseRedirect(reverse("dashboard:payment_detail", kwargs={"id": payment.id}))
