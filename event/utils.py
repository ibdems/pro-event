import uuid

import requests
from django.conf import settings
from django.urls import reverse


def generer_reference():
    return str(uuid.uuid4())


def create_lengopay_payment(request, amount, currency=None):
    """
    Crée un paiement via l'API Lengo Pay (Cash out - Collect payments).
    Retourne (result_dict, pay_id) en cas de succès.
    """
    base_url = getattr(settings, "LENGOPAY_API_BASE_URL", "https://sandbox.lengopay.com").rstrip(
        "/"
    )
    url = f"{base_url}/api/v1/payments"
    website_id = getattr(settings, "LENGOPAY_WEBSITE_ID", "")
    license_key = getattr(settings, "LENGOPAY_LICENSE_KEY", "")
    currency = currency or getattr(settings, "LENGOPAY_CURRENCY", "GNF")

    callback_url = request.build_absolute_uri(reverse("event:lengopay_callback"))
    return_url = request.build_absolute_uri(reverse("event:lengopay_return"))
    failure_url = request.build_absolute_uri(reverse("event:lengopay_return"))

    headers = {
        "Authorization": f"Basic {license_key}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    payload = {
        "websiteid": website_id,
        "amount": int(amount),
        "currency": currency,
        "callback_url": callback_url,
        "return_url": return_url,
        "failure_url": failure_url,
    }

    response = requests.post(url, json=payload, headers=headers, timeout=30)
    result = response.json()

    pay_id = result.get("pay_id") or result.get("payment_id")
    payment_url = result.get("payment_url")

    if response.status_code == 200 and payment_url and pay_id:
        return result, pay_id

    return result, None


def check_lengopay_status(pay_id):
    """
    Vérifie le statut d'un paiement Lengo Pay (POST /api/v1/transaction/status).
    """
    base_url = getattr(settings, "LENGOPAY_API_BASE_URL", "https://sandbox.lengopay.com").rstrip(
        "/"
    )
    url = f"{base_url}/api/v1/transaction/status"
    website_id = getattr(settings, "LENGOPAY_WEBSITE_ID", "")
    license_key = getattr(settings, "LENGOPAY_LICENSE_KEY", "")

    headers = {
        "Authorization": f"Basic {license_key}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    payload = {
        "pay_id": pay_id,
        "websiteid": website_id,
    }

    response = requests.post(url, json=payload, headers=headers, timeout=15)
    return response.json()
