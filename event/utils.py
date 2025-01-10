from .models import Ticket


def verify_ticket(code):
    ticket = Ticket.objects.filter(code_ticket=code).first()
    if not ticket:
        return "Invalid Ticket"
    ticket.scan_count += 1
    ticket.save()
    return f"Ticket valid, scanned {ticket.scan_count} times"
