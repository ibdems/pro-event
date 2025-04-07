from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from django.views.generic import TemplateView

from demande.models import Demande
from event.models import Contact, Event, Payement, Ticket
from users.models import User


class DashboardHomeView(LoginRequiredMixin, TemplateView):
    """Vue principale du tableau de bord"""

    template_name = "dashboard/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if self.request.user.is_staff or self.request.user.is_superuser:
            # Statistiques pour les administrateurs
            total_events = Event.objects.count()
            total_users = User.objects.count()
            total_tickets = Ticket.objects.count()
            total_payments = Payement.objects.count()
            total_demandes = Demande.objects.count()
            unread_contacts = Contact.objects.filter(is_read=False).count()

            # Graphiques pour les administrateurs
            events_by_category = dict(
                Event.objects.values("category__name")
                .annotate(count=Count("id"))
                .values_list("category__name", "count")
            )
            tickets_by_type = dict(
                Ticket.objects.values("type_ticket")
                .annotate(count=Count("id"))
                .values_list("type_ticket", "count")
            )

            context.update(
                {
                    "total_events": total_events,
                    "total_users": total_users,
                    "total_tickets": total_tickets,
                    "total_payments": total_payments,
                    "total_demandes": total_demandes,
                    "unread_contacts": unread_contacts,
                    "events_by_category": events_by_category,
                    "tickets_by_type": tickets_by_type,
                    "recent_events": Event.objects.order_by("-created_at")[:5],
                    "recent_demandes": Demande.objects.order_by("-id")[:5],
                    "recent_contacts": Contact.objects.order_by("-created_at")[:5],
                }
            )
        else:
            # Statistiques pour les organisateurs
            user_events = Event.objects.filter(user=self.request.user)
            total_user_events = user_events.count()
            total_user_tickets = Ticket.objects.filter(event__user=self.request.user).count()
            total_user_payments = Payement.objects.filter(event__user=self.request.user).count()

            context.update(
                {
                    "total_events": total_user_events,
                    "total_tickets": total_user_tickets,
                    "total_payments": total_user_payments,
                    "recent_events": user_events.order_by("-created_at")[:5],
                }
            )

        return context
