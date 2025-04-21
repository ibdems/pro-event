from uuid import UUID

from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views import View

from event.models import Event, Ticket


class ScanCodeView(View):
    def get(self, request, event_id):
        event = get_object_or_404(Event, uid=event_id)
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
        except Exception:
            return JsonResponse(
                {"success": False, "message": "Une erreur est survenue lors de la vérification."}
            )


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
