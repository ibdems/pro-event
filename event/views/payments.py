from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from event.models import Payement
from event.utils import check_paycard_status
from event.tasks import generate_and_save_ticket_pdf, send_ticket_by_email, send_ticket_by_whatsapp
from celery import chord, group

@csrf_exempt
def paycard_callback(request, reference):
    result = check_paycard_status(reference)
    payement = get_object_or_404(Payement, operation_reference=reference)
    if result.get("code") == 0 and result.get("status") == "success":
        payement.statut_payement = "valide"
        payement.save()
        # Générer les tickets ici (logique existante)
        event = payement.event
        info_ticket = event.infoticket_event
        quantities = {
            "normal": getattr(payement, "quantity_normal", 0) if hasattr(payement, "quantity_normal") else 0,
            "vip": getattr(payement, "quantity_vip", 0) if hasattr(payement, "quantity_vip") else 0,
            "vvip": getattr(payement, "quantity_vvip", 0) if hasattr(payement, "quantity_vvip") else 0,
        }
        tasks = []
        for type_ticket, quantite in quantities.items():
            if quantite > 0:
                for _ in range(quantite):
                    # La logique métier de création de ticket doit être ici
                    from event.models import Ticket
                    ticket = Ticket.objects.create(
                        payement=payement, event=event, type_ticket=type_ticket
                    )
                    tasks.append(
                        generate_and_save_ticket_pdf.s(event.id, ticket.id, payement.id)
                    )
        def send_email_or_whatsapp():
            if payement.payment_method == "email":
                callback = send_ticket_by_email.si(payement.id)
            else:
                callback = send_ticket_by_whatsapp.si(payement.id)
            chord(group(tasks))(callback)
        if tasks:
            send_email_or_whatsapp()
        return render(request, "event/payment_return.html", {"status": "success", "payement": payement})
    else:
        payement.statut_payement = "echec"
        payement.save()
        return render(request, "event/payment_return.html", {"status": "failed", "payement": payement, "error": result.get("error_message", "")}) 