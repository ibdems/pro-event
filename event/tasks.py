import logging

from celery import shared_task
from celery.exceptions import MaxRetriesExceededError
from django.core.files.base import ContentFile
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from weasyprint import HTML

from .models import Event, Payement, Ticket

logger = logging.getLogger("celery")


@shared_task(bind=True, max_retries=3)
def generate_and_save_ticket_pdf(self, event_id, ticket_id, payement_id):
    """Generate and save ticket PDF asynchronously"""
    try:
        event = Event.objects.get(id=event_id)
        ticket = Ticket.objects.get(id=ticket_id)
        payement = Payement.objects.get(id=payement_id)

        html_content = render_to_string(
            "event/ticket_vertical.html", {"event": event, "ticket": ticket, "payement": payement}
        )

        pdf_content = HTML(string=html_content).write_pdf()

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
                email.attach_file(ticket.ticket_pdf.path)

        email.send()
        return True

    except Exception as e:
        logger.error(f"Erreur d'envoi d'email pour le paiement {payement_id}: {e}")
        try:
            raise self.retry(exc=e, countdown=15)
        except MaxRetriesExceededError:
            logger.critical(f"Échec définitif d'envoi d'email pour le paiement {payement_id}")
            raise
