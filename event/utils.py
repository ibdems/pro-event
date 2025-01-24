from django.conf import settings
from django.core.files.base import ContentFile
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from weasyprint import HTML


def generate_ticket_pdf(event, ticket, payement):
    """
    Generate ticket PDF using WeasyPrint.
    """
    try:
        # Render template with full context
        html_content = render_to_string(
            "event/ticket_vertical.html", {"event": event, "ticket": ticket, "payement": payement}
        )

        # Generate PDF using WeasyPrint
        try:
            # Convert HTML to PDF
            pdf_content = HTML(string=html_content, base_url=settings.BASE_DIR).write_pdf()
            return pdf_content
        except Exception as pdf_error:
            print(f"PDF generation error: {pdf_error}")
            print("HTML Content:", html_content)
            raise

    except Exception as e:
        print(f"Ticket PDF generation failed: {e}")
        raise


def save_ticket_pdf(ticket, event, payement):
    """
    Save the generated PDF to the ticket model.
    """
    pdf_content = generate_ticket_pdf(event, ticket, payement)
    file_name = f"ticket_{ticket.code_ticket}.pdf"
    ticket.ticket_pdf.save(file_name, ContentFile(pdf_content))


def send_ticket_by_email(payement, tickets):
    """
    Envoie les tickets par email.
    """
    subject = f"Vos tickets pour l'événement {payement.event.title}"
    message = f"""
    Bonjour {payement.nom_complet},

    Merci pour votre achat. Veuillez trouver ci-joint votre/vos ticket(s) pour
    l'événement {payement.event.title}.

    Nous sommes impatients de vous accueillir.

    Gardez soigneusement le/les ticket(s).

    Cordialement,
    L'équipe ProEvent

    """

    email = EmailMessage(subject, message, "contact@proevent.com", [payement.email_reception])

    for ticket in tickets:
        pdf_content = generate_ticket_pdf(payement.event, ticket, payement)
        email.attach(f"ticket_{ticket.code_ticket}.pdf", pdf_content, "application/pdf")

    email.send()
