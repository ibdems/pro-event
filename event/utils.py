import uuid
import requests
from django.conf import settings
from django.urls import reverse

def generer_reference():
    return str(uuid.uuid4())

def create_paycard_payment(request, montant, description, payment_method):
    url = "https://mapaycard.com/epay/create/"
    reference = generer_reference()
    callback_url = request.build_absolute_uri(
        reverse('event:paycard_callback', args=[reference])
    )
    data = {
        "c": settings.PAYCARD_ECOMMERCE_CODE,
        "paycard-amount": montant,
        "paycard-description": description,
        "paycard-operation-reference": reference,
        "paycard-callback-url": callback_url,
        "paycard-auto-redirect": "off",
        "paycard-redirect-with-get": "on",
    }
    if payment_method == "paycard":
        data["paycard-jump-to-paycard"] = "on"
    elif payment_method == "visa":
        data["paycard-jump-to-cc"] = "on"
    elif payment_method == "orange_money":
        data["paycard-jump-to-om"] = "on"
    elif payment_method == "mobile_money":
        data["paycard-jump-to-momo"] = "on"

    response = requests.post(url, data=data)
    result = response.json()
    return result, reference

def check_paycard_status(reference):
    url = f"https://mapaycard.com/epay/{settings.PAYCARD_ECOMMERCE_CODE}/{reference}/status"
    response = requests.get(url)
    return response.json() 