import json
import logging

from celery import chain, group
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from event.models import Payement, Ticket
from event.tasks import (
    generate_and_save_ticket_pdf,
    send_ticket_by_email,
    send_ticket_by_whatsapp,
)

logger = logging.getLogger(__name__)


def _process_successful_payment(payement):
    """Crée les tickets et lance la génération PDF + envoi email/WhatsApp."""
    event = payement.event
    quantities = {
        "normal": payement.quantity_normal,
        "vip": payement.quantity_vip,
        "vvip": payement.quantity_vvip,
    }
    tasks = []
    for type_ticket, quantite in quantities.items():
        if quantite > 0:
            for _ in range(quantite):
                ticket = Ticket.objects.create(
                    payement=payement, event=event, type_ticket=type_ticket
                )
                tasks.append(generate_and_save_ticket_pdf.s(event.id, ticket.id, payement.id))

    if tasks:
        if payement.email_reception:
            workflow = chain(group(tasks), send_ticket_by_email.si(payement.id))
            workflow.apply_async()
        elif payement.telephone_reception:
            for task in tasks:
                task.delay()
            send_ticket_by_whatsapp.delay(payement.id)
        else:
            for task in tasks:
                task.delay()


@csrf_exempt
@require_http_methods(["POST"])
def lengopay_callback(request):
    """
    Callback server-to-server Lengo Pay (POST JSON).
    Body: pay_id, status (SUCCESS | FAILED), amount, message, Client (optionnel).
    """
    try:
        body = json.loads(request.body.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        logger.warning("lengopay_callback: body invalide %s", e)
        return JsonResponse({"status": "error", "message": "Invalid JSON"}, status=400)

    pay_id = body.get("pay_id")
    status = (body.get("status") or "").upper()

    if not pay_id:
        return JsonResponse({"status": "error", "message": "pay_id required"}, status=400)

    payement = Payement.objects.filter(operation_reference=pay_id).first()
    if not payement:
        logger.warning("lengopay_callback: Payement introuvable pay_id=%s", pay_id)
        return JsonResponse({"status": "error", "message": "Payment not found"}, status=404)

    if status == "SUCCESS":
        if payement.statut_payement != "valide":
            payement.statut_payement = "valide"
            payement.save()
            _process_successful_payment(payement)
    elif status == "FAILED":
        payement.statut_payement = "echec"
        payement.save()
    else:
        logger.info("lengopay_callback: statut ignoré pay_id=%s status=%s", pay_id, status)

    return JsonResponse({"status": "ok"})


@require_http_methods(["GET"])
def lengopay_return(request):
    """
    Page de retour après paiement (return_url / failure_url).
    - Si pay_id en GET ou en session : on récupère le paiement.
    - Si le paiement est encore "en_attente", on vérifie le statut auprès de Lengo Pay
      (fallback quand le callback serveur n'est pas reçu, ex. en local).
    """
    from event.utils import check_lengopay_status

    pay_id = request.GET.get("pay_id") or request.session.pop("lengopay_pay_id", None)
    payement = None
    if pay_id:
        payement = Payement.objects.filter(operation_reference=pay_id).first()

        if payement and payement.statut_payement == "en_attente":
            result = check_lengopay_status(pay_id)
            api_status = (result.get("status") or "").upper()
            if api_status == "SUCCESS":
                payement.statut_payement = "valide"
                payement.save()
                _process_successful_payment(payement)
                logger.info("lengopay_return: paiement validé via API (pay_id=%s)", pay_id)
            elif api_status == "FAILED":
                payement.statut_payement = "echec"
                payement.save()
                logger.info("lengopay_return: paiement en échec via API (pay_id=%s)", pay_id)

    if payement:
        status = "success" if payement.statut_payement == "valide" else "failed"
        if payement.statut_payement == "en_attente":
            status = "pending"
        return render(
            request,
            "event/payment_return.html",
            {
                "status": status,
                "payement": payement,
                "error": "" if status != "failed" else "Le paiement n'a pas abouti.",
            },
        )

    return render(
        request,
        "event/payment_return.html",
        {
            "status": "pending",
            "payement": None,
            "error": "",
        },
    )
