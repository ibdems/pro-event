import base64
import logging
import os

import requests
from celery import shared_task
from celery.exceptions import MaxRetriesExceededError
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.utils import timezone
from weasyprint import HTML

from .models import Event, Invitation, Payement, Ticket

logger = logging.getLogger("celery")


@shared_task(bind=True, max_retries=3)
def generate_and_save_ticket_pdf(self, event_id, ticket_id, payement_id):
    """Generate and save ticket PDF asynchronously"""
    try:
        event = Event.objects.get(id=event_id)
        ticket = Ticket.objects.get(id=ticket_id)
        payement = Payement.objects.get(id=payement_id)

        # Obtenir le domaine depuis les paramètres
        site_url = getattr(settings, "DOMAIN_URL", "https://proeventgn.com")

        # Contexte avec le domaine pour les URLs absolues
        # Pour S3/Backblaze, les URLs sont déjà complètes, pas besoin de les préfixer
        context = {
            "event": event,
            "ticket": ticket,
            "payement": payement,
            "domain": site_url,
            "absolute_static_url": site_url
            + settings.STATIC_URL,  # Pour les fichiers statiques locaux
            "absolute_media_url": "",  # Les fichiers médias S3 ont déjà des URLs complètes
        }

        html_content = render_to_string("event/ticket_vertical.html", context)

        pdf_content = HTML(string=html_content, base_url=site_url).write_pdf()

        file_name = f"ticket_{ticket.code_ticket}.pdf"
        ticket.ticket_pdf.save(file_name, ContentFile(pdf_content))

        # Return both ticket_id and payment_id
        return {"ticket_id": ticket_id, "payement_id": payement_id}

    except Exception as e:
        logger.error(f"PDF generation error for ticket {ticket_id}: {e}")
        try:
            raise self.retry(exc=e, countdown=10)
        except MaxRetriesExceededError:
            logger.critical(f"Final PDF generation failure for ticket {ticket_id}")
            raise


@shared_task(bind=True, max_retries=3)
def send_ticket_by_email(self, payement_id, result=None):
    print(f"No payement recu {payement_id} et type: {type(payement_id)}")
    """Envoie les tickets générés par email"""
    try:
        payement = Payement.objects.get(id=payement_id)
        tickets = Ticket.objects.filter(payement=payement)

        if not tickets.exists():
            logger.error(f"Aucun ticket trouvé pour le paiement {payement_id}")
            return

        subject = f"Vos tickets pour {payement.event.title}"
        message = f"""
        Bonjour {payement.nom_complet},

        Merci pour votre achat. Veuillez trouver ci-joint vos tickets pour
        {payement.event.title}.

        Cordialement,
        L'équipe ProEvent
        """

        email = EmailMessage(subject, message, "contact@proevent.com", [payement.email_reception])

        for ticket in tickets:
            if ticket.ticket_pdf:
                response = requests.get(ticket.ticket_pdf.url)
                if response.status_code == 200:
                    email.attach(
                        filename=os.path.basename(ticket.ticket_pdf.name),
                        content=response.content,
                        mimetype="application/pdf",
                    )

        email.send()
        return True

    except Exception as e:
        logger.error(f"Erreur d'envoi d'email pour le paiement {payement_id}: {e}")
        try:
            raise self.retry(exc=e, countdown=15)
        except MaxRetriesExceededError:
            logger.critical(f"Échec définitif d'envoi d'email pour le paiement {payement_id}")
            raise


@shared_task(bind=True, max_retries=3)
def send_invitation_email(self, invitation_id):
    """Envoie un email d'invitation pour un événement privé"""
    try:
        invitation = Invitation.objects.get(id=invitation_id)
        event = invitation.event

        # Construire l'URL avec le token pour accepter/refuser
        base_url = getattr(settings, "DOMAIN_URL", "https://proeventgn.com")
        accept_url = f"https://{base_url}/invitation/{invitation.token}/accept/"
        decline_url = f"https://{base_url}/invitation/{invitation.token}/decline/"

        context = {
            "invitation": invitation,
            "event": event,
            "accept_url": accept_url,
            "decline_url": decline_url,
        }

        # Récupérer le contenu HTML pour l'email
        html_content = render_to_string("event/emails/invitation.html", context)

        subject = f"Invitation: {event.title}"

        email = EmailMessage(
            subject,
            html_content,
            "invitations@proevent.com",
            [invitation.email],
        )
        email.content_subtype = "html"  # Main content is now HTML
        email.send()

        # Mettre à jour la date d'envoi
        invitation.sent_at = timezone.now()
        invitation.save()

        return True

    except Exception as e:
        logger.error(f"Erreur d'envoi d'invitation pour invitation_id {invitation_id}: {e}")
        try:
            raise self.retry(exc=e, countdown=10)
        except MaxRetriesExceededError:
            logger.critical(
                f"Échec définitif d'envoi d'invitation pour invitation_id {invitation_id}"
            )
            raise


@shared_task(bind=True, max_retries=3)
def generate_and_send_invitation_ticket(self, invitation_id):
    """Génère et envoie un ticket après acceptation d'une invitation"""
    try:
        invitation = Invitation.objects.get(id=invitation_id)

        if not invitation.ticket:
            logger.error(f"Aucun ticket associé à l'invitation {invitation_id}")
            return False

        ticket = invitation.ticket
        payement = ticket.payement
        event = ticket.event

        # Obtenir le domaine depuis les paramètres
        site_url = getattr(settings, "DOMAIN_URL", "https://proeventgn.com")

        # Contexte avec le domaine pour les URLs absolues
        context = {
            "event": event,
            "ticket": ticket,
            "payement": payement,
            "is_invitation": True,
            "domain": site_url,
            "absolute_media_url": "",
        }

        # Générer le PDF du ticket
        html_content = render_to_string("event/ticket_vertical.html", context)

        pdf_content = HTML(string=html_content, base_url=site_url).write_pdf()

        file_name = f"invitation_ticket_{ticket.code_ticket}.pdf"
        ticket.ticket_pdf.save(file_name, ContentFile(pdf_content))

        # Envoyer le ticket par email
        subject = f"Votre ticket pour {event.title}"
        message = f"""
        Bonjour {invitation.name},

        Merci d'avoir accepté notre invitation à l'événement "{event.title}".
        Votre ticket est joint à cet email.

        Date: {event.start_date.strftime('%d/%m/%Y à %H:%M')}
        Lieu: {event.location}
        Type de ticket: {ticket.get_type_ticket_display()}

        Nous avons hâte de vous y voir!

        Cordialement,
        L'équipe ProEvent
        """

        email = EmailMessage(subject, message, "tickets@proevent.com", [invitation.email])

        if ticket.ticket_pdf:
            response = requests.get(ticket.ticket_pdf.url)
            if response.status_code == 200:
                email.attach(
                    filename=os.path.basename(ticket.ticket_pdf.name),
                    content=response.content,
                    mimetype="application/pdf",
                )

        email.send()
        return True

    except Exception as e:
        logger.error(f"Erreur de génération/envoi de ticket pour invitation {invitation_id}: {e}")
        try:
            raise self.retry(exc=e, countdown=15)
        except MaxRetriesExceededError:
            logger.critical(
                f"Échec définitif de génération/envoi de ticket pour invitation {invitation_id}"
            )
            raise


@shared_task(bind=True, max_retries=3)
def send_demande_accepted_email(self, demande_id, password=None):
    """Envoie un email de notification d'acceptation de demande"""
    from demande.models import Demande
    from demande.utils import send_demande_accepted_email as send_email

    try:
        demande = Demande.objects.get(uid=demande_id)
        send_email(demande, password)
        return True

    except Exception as e:
        logger.error(f"Erreur d'envoi d'email d'acceptation pour demande {demande_id}: {e}")
        try:
            raise self.retry(exc=e, countdown=10)
        except MaxRetriesExceededError:
            logger.critical(
                f"Échec définitif d'envoi d'email d'acceptation pour demande {demande_id}"
            )
            raise


@shared_task(bind=True, max_retries=3)
def send_demande_rejected_email(self, demande_id):
    """Envoie un email de notification de rejet de demande"""
    from demande.models import Demande
    from demande.utils import send_demande_rejected_email as send_email

    try:
        demande = Demande.objects.get(uid=demande_id)
        send_email(demande)
        return True

    except Exception as e:
        logger.error(f"Erreur d'envoi d'email de rejet pour demande {demande_id}: {e}")
        try:
            raise self.retry(exc=e, countdown=10)
        except MaxRetriesExceededError:
            logger.critical(f"Échec définitif d'envoi d'email de rejet pour demande {demande_id}")
            raise


@shared_task(bind=True, max_retries=3)
def send_ticket_by_whatsapp(self, payement_id, result=None):
    """Envoie les tickets générés par WhatsApp"""
    try:
        payement = Payement.objects.get(id=payement_id)
        tickets = Ticket.objects.filter(payement=payement)

        if not tickets.exists():
            logger.error(f"Aucun ticket trouvé pour le paiement {payement_id}")
            return

        # Contenu du message
        message_text = f"""
        Bonjour {payement.nom_complet},

        Merci pour votre achat. Voici votre(vos) ticket(s)
        pour l'événement : {payement.event.title}.

        Cordialement,
        L'équipe ProEvent
        """  # noqa

        # Formater le numéro de téléphone (enlever les espaces, ajouter l'indicatif pays si besoin)
        phone_number = payement.telephone_reception.strip()
        if not phone_number.startswith("+"):
            # Assumant que c'est un numéro guinéen si pas d'indicatif (ajouter +224)
            if phone_number.startswith("0"):
                phone_number = "+224" + phone_number[1:]
            else:
                phone_number = "+224" + phone_number

        # Envoyer un message pour chaque ticket
        success = True
        for ticket in tickets:
            if ticket.ticket_pdf and os.path.exists(ticket.ticket_pdf.path):
                try:
                    # Lire le fichier PDF en tant que bytes
                    with open(ticket.ticket_pdf.path, "rb") as pdf_file:
                        pdf_bytes = pdf_file.read()

                    # Encodage en base64
                    pdf_base64 = base64.b64encode(pdf_bytes).decode("utf-8")  # noqa

                    # Simuler l'appel à l'API WhatsApp Business
                    # Dans un environnement réel, cela ressemblerait à:
                    """
                    response = requests.post(
                        "https://graph.facebook.com/v17.0/YOUR_PHONE_NUMBER_ID/messages",
                        headers={
                            "Authorization": f"Bearer {settings.WHATSAPP_API_TOKEN}",
                            "Content-Type": "application/json"
                        },
                        json={
                            "messaging_product": "whatsapp",
                            "recipient_type": "individual",
                            "to": phone_number,
                            "type": "document",
                            "document": {
                                "filename": f"ticket_{ticket.code_ticket}.pdf",
                                "caption": message_text,
                                "link": f"https://{settings.DOMAIN_URL}{ticket.ticket_pdf.url}"
                            }
                        }
                    )

                    if response.status_code != 200:
                        logger.error(f"Échec de l'envoi WhatsApp: {response.text}")
                        success = False
                    """
                except Exception as e:
                    logger.error(
                        f"Erreur lors de l'envoi du ticket {ticket.code_ticket} par WhatsApp: {e}"
                    )
                    success = False
            else:
                logger.error(f"Pas de PDF disponible pour le ticket {ticket.code_ticket}")
                success = False

        return success

    except Exception as e:
        logger.error(f"Erreur d'envoi WhatsApp pour le paiement {payement_id}: {e}")
        try:
            raise self.retry(exc=e, countdown=15)
        except MaxRetriesExceededError:
            logger.critical(f"Échec définitif d'envoi WhatsApp pour le paiement {payement_id}")
            raise
