from celery import chain, group
from django.shortcuts import get_object_or_404, render
from django.views.decorators.csrf import csrf_exempt

from event.models import Payement
from event.tasks import (
    generate_and_save_ticket_pdf,
    send_ticket_by_email,
    send_ticket_by_whatsapp,
)
from event.utils import check_paycard_status


@csrf_exempt
def paycard_callback(request, reference):
    result = check_paycard_status(reference)

    payement = get_object_or_404(Payement, operation_reference=reference)

    if result.get("code") == 0 and result.get("status") == "success":
        payement.statut_payement = "valide"
        payement.save()

        event = payement.event

        quantities = {
            "normal": payement.quantity_normal,
            "vip": payement.quantity_vip,
            "vvip": payement.quantity_vvip,
        }

        tasks = []
        for type_ticket, quantite in quantities.items():
            if quantite > 0:
                # print(f"[DEBUG] Création de {quantite} tickets {type_ticket}")
                for _ in range(quantite):
                    from event.models import Ticket

                    ticket = Ticket.objects.create(
                        payement=payement, event=event, type_ticket=type_ticket
                    )
                    # print(f"[DEBUG] Ticket créé avec ID:", ticket.id)
                    tasks.append(generate_and_save_ticket_pdf.s(event.id, ticket.id, payement.id))

        def send_email_or_whatsapp():
            if payement.email_reception:
                # Chaînage : d'abord tous les PDFs, puis l'email
                workflow = chain(group(tasks), send_ticket_by_email.si(payement.id))
                workflow.apply_async()
            elif payement.telephone_reception:
                for task in tasks:
                    task.delay()
                send_ticket_by_whatsapp.delay(payement.id)
            else:
                for task in tasks:
                    task.delay()

        if tasks:
            send_email_or_whatsapp()

        return render(
            request, "event/payment_return.html", {"status": "success", "payement": payement}
        )
    else:
        payement.statut_payement = "echec"
        payement.save()
        return render(
            request,
            "event/payment_return.html",
            {"status": "failed", "payement": payement, "error": result.get("error_message", "")},
        )
