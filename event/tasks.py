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
def generate_ticket_pdf(self, event_id, ticket_id, payement_id):
    try:
        event = Event.objects.get(id=event_id)
        ticket = Ticket.objects.get(id=ticket_id)
        payement = Payement.objects.get(id=payement_id)

        html_content = render_to_string(
            "event/ticket_vertical.html", {"event": event, "ticket": ticket, "payement": payement}
        )
        pdf_content = HTML(string=html_content).write_pdf()
        return pdf_content
    except Exception as e:
        logger.error(f"Erreur lors de la génération du PDF pour le ticket {ticket_id}: {e}")
        try:
            raise self.retry(exc=e, countdown=10)
        except MaxRetriesExceededError:
            logger.critical(f"Échec définitif de la génération du PDF pour le ticket {ticket_id}.")
            raise


@shared_task(bind=True, max_retries=3)
def save_ticket_pdf(self, ticket_id, event_id, payement_id):
    try:
        ticket = Ticket.objects.get(id=ticket_id)
        pdf_content = generate_ticket_pdf(event_id, ticket_id, payement_id)
        file_name = f"ticket_{ticket.code_ticket}.pdf"
        ticket.ticket_pdf.save(file_name, ContentFile(pdf_content))
    except Exception as e:
        logger.error(f"Erreur lors de la sauvegarde du PDF pour le ticket {ticket_id}: {e}")
        try:
            raise self.retry(exc=e, countdown=10)
        except MaxRetriesExceededError:
            logger.critical(f"Échec définitif de la sauvegarde du PDF pour le ticket {ticket_id}.")
            raise


@shared_task(bind=True, max_retries=3)
def send_ticket_by_email(self, payement_id):
    try:
        payement = Payement.objects.get(id=payement_id)
        tickets = Ticket.objects.filter(payement=payement)

        subject = f"Vos tickets pour l'événement {payement.event.title}"
        message = f"""
        Bonjour {payement.nom_complet},

        Merci pour votre achat. Veuillez trouver ci-joint votre/vos ticket(s) pour
        l'événement {payement.event.title}.

        Cordialement,
        L'équipe ProEvent
        """

        email = EmailMessage(subject, message, "contact@proevent.com", [payement.email_reception])

        for ticket in tickets:
            if ticket.ticket_pdf:
                email.attach_file(ticket.ticket_pdf.path)

        email.send()
    except Exception as e:
        logger.error(f"Erreur lors de l'envoi des emails pour le paiement {payement_id}: {e}")
        try:
            raise self.retry(exc=e, countdown=15)
        except MaxRetriesExceededError:
            logger.critical(
                f"Échec définitif de l'envoi des emails pour le paiement {payement_id}."
            )
            raise
