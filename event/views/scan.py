from uuid import UUID

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views import View

from event.models import Event, EventScanner, Ticket
from users.models import User


class ScanCodeView(LoginRequiredMixin, View):
    def get(self, request, event_id):
        event = get_object_or_404(Event, uid=event_id)

        # Vérifier l'autorisation de l'utilisateur
        if not EventScanner.is_user_authorized(request.user, event):
            messages.error(
                request, "Vous n'êtes pas autorisé à scanner les tickets pour cet événement."
            )
            return redirect("event:home")

        disponibilite = event.get_disponibilite()
        tickets_scannes = event.ticket_event.filter(scan_count__gt=0).count()

        if disponibilite:
            total_capacite = (
                disponibilite["normal"]["capacite"]
                + disponibilite["vip"]["capacite"]
                + disponibilite["vvip"]["capacite"]
            )
            tickets_disponibles = (
                disponibilite["normal"]["disponibles"]
                + disponibilite["vip"]["disponibles"]
                + disponibilite["vvip"]["disponibles"]
            )
        else:
            total_capacite = 0
            tickets_disponibles = 0

        context = {
            "event": event,
            "total_capacity": total_capacite,
            "tickets_scanned": tickets_scannes,
            "available_capacity": tickets_disponibles,
        }
        return render(request, "event/scan_ticket.html", context)

    def post(self, request, event_id):
        event = get_object_or_404(Event, uid=event_id)

        # Vérifier l'autorisation de l'utilisateur
        if not EventScanner.is_user_authorized(request.user, event):
            return JsonResponse(
                {
                    "success": False,
                    "message": "Vous n'êtes pas autorisé à scanner les tickets pour cet événement.",
                }
            )

        code_ticket = request.POST.get("code_ticket")
        print(f"Code ticket {code_ticket}")
        try:
            ticket = Ticket.objects.get(code_ticket=code_ticket)
            print(f"ticket: {ticket}")

            event_id = UUID(event_id)
            print(f"type(event_id): {type(event_id)}, value: {event_id}")
            print(f"type(ticket.event.uid): {type(ticket.event.uid)}, value: {ticket.event.uid}")
            if ticket.event.uid != event_id:
                return JsonResponse(
                    {"success": False, "message": "Ce ticket n'est pas valide pour cet événement."}
                )

            if not ticket.event.statut:
                return JsonResponse(
                    {"success": False, "message": "Cet événement n'est plus actif."}
                )

            if ticket.event.end_date < timezone.now():
                return JsonResponse({"success": False, "message": "Cet événement est terminé."})

            if ticket.scan_count > 0:
                return JsonResponse(
                    {
                        "success": False,
                        "message": f"Attention: Ce ticket a déjà été scanné"
                        f" {ticket.scan_count} fois.",
                        "type_ticket": ticket.type_ticket,
                        "scan_count": ticket.scan_count,
                    }
                )

            ticket.scan_count += 1
            ticket.save()

            return JsonResponse(
                {
                    "success": True,
                    "message": "Ticket valide.",
                    "type_ticket": ticket.type_ticket,
                    "scan_count": ticket.scan_count,
                }
            )

        except Ticket.DoesNotExist:
            return JsonResponse({"success": False, "message": "Ticket invalide ou inexistant."})


class EventScannerListView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Vue pour lister les scanners d'un événement"""

    def test_func(self):
        event = get_object_or_404(Event, uid=self.kwargs.get("event_id"))
        return (
            self.request.user.is_staff
            or self.request.user.is_superuser
            or event.user == self.request.user
        )

    def get(self, request, event_id):
        event = get_object_or_404(Event, uid=event_id)
        scanners = EventScanner.objects.filter(event=event).select_related("user")

        context = {
            "event": event,
            "scanners": scanners,
        }
        return render(request, "event/scanner_list.html", context)


class EventScannerAddView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Vue pour ajouter un scanner à un événement"""

    def test_func(self):
        event = get_object_or_404(Event, uid=self.kwargs.get("event_id"))
        return (
            self.request.user.is_staff
            or self.request.user.is_superuser
            or event.user == self.request.user
        )

    def get(self, request, event_id):
        event = get_object_or_404(Event, uid=event_id)
        # Récupérer tous les utilisateurs qui ne sont pas déjà scanners pour cet événement
        existing_scanners = EventScanner.objects.filter(event=event).values_list(
            "user_id", flat=True
        )
        available_users = User.objects.filter(is_active=True, role="scanner").exclude(
            id__in=existing_scanners
        )

        context = {
            "event": event,
            "available_users": available_users,
        }
        return render(request, "event/scanner_add.html", context)

    def post(self, request, event_id):
        event = get_object_or_404(Event, uid=event_id)
        user_id = request.POST.get("user_id")

        if not user_id:
            messages.error(request, "Veuillez sélectionner un utilisateur.")
            return redirect("event:scanner_add", event_id=event_id)

        try:
            user = User.objects.get(id=user_id, is_active=True)

            # Vérifier si l'utilisateur n'est pas déjà scanner
            if EventScanner.objects.filter(event=event, user=user).exists():
                messages.error(request, "Cet utilisateur est déjà scanner pour cet événement.")
                return redirect("event:scanner_add", event_id=event_id)

            # Créer le scanner
            EventScanner.objects.create(event=event, user=user, created_by=request.user)

            messages.success(request, f"{user.get_full_name()} a été ajouté comme scanner.")
            return redirect("event:scanner_list", event_id=event_id)

        except User.DoesNotExist:
            messages.error(request, "Utilisateur introuvable.")
            return redirect("event:scanner_add", event_id=event_id)


class EventScannerRemoveView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Vue pour retirer un scanner d'un événement"""

    def test_func(self):
        event = get_object_or_404(Event, uid=self.kwargs.get("event_id"))
        return (
            self.request.user.is_staff
            or self.request.user.is_superuser
            or event.user == self.request.user
        )

    def post(self, request, event_id):
        event = get_object_or_404(Event, uid=event_id)
        scanner_id = request.POST.get("scanner_id")

        try:
            scanner = EventScanner.objects.get(id=scanner_id, event=event)
            user_name = scanner.user.get_full_name()
            scanner.delete()
            messages.success(request, f"{user_name} a été retiré des scanners.")
        except EventScanner.DoesNotExist:
            messages.error(request, "Scanner introuvable.")

        return redirect("event:scanner_list", event_id=event_id)


class CheckTicketView(View):
    def get(self, request, code):
        try:
            ticket = Ticket.objects.select_related("event", "payement").get(code=code)
            if ticket.is_used:
                return JsonResponse(
                    {"valid": False, "message": "Ce ticket a déjà été utilisé.", "ticket": None}
                )

            # Retourner les informations du ticket
            return JsonResponse(
                {
                    "valid": True,
                    "message": "Ticket valide",
                    "ticket": {
                        "id": ticket.id,
                        "code": ticket.code,
                        "event_title": ticket.event.title,
                        "event_date": ticket.event.start_date.strftime("%d/%m/%Y"),
                        "type_ticket": ticket.type_ticket,
                        "full_name": ticket.payement.fullname,
                        "is_used": ticket.is_used,
                    },
                }
            )
        except Ticket.DoesNotExist:
            return JsonResponse({"valid": False, "message": "Ticket introuvable", "ticket": None})

    def post(self, request, code):
        try:
            ticket = Ticket.objects.select_related("event").get(code=code)
            if ticket.is_used:
                return JsonResponse({"success": False, "message": "Ce ticket a déjà été utilisé."})

            # Marquer le ticket comme utilisé
            ticket.is_used = True
            ticket.used_at = timezone.now()
            ticket.save(update_fields=["is_used", "used_at"])

            return JsonResponse({"success": True, "message": "Ticket validé avec succès."})
        except Ticket.DoesNotExist:
            return JsonResponse({"success": False, "message": "Ticket introuvable"})
