from django.contrib import messages
from django.shortcuts import redirect
from django.utils import timezone
from django.views import View

from event.models import Invitation


class InvitationResponseView(View):
    def get_invitation(self, token, action):
        try:
            invitation = Invitation.objects.get(token=token)
            if invitation.status != "pending":
                messages.info(self.request, "Vous avez déjà répondu à cette invitation.")
                return None
            return invitation
        except Invitation.DoesNotExist:
            messages.error(self.request, "Invitation non valide ou expirée.")
            return None

    def get(self, request, *args, **kwargs):
        token = kwargs.get("token")
        action = kwargs.get("action")

        if action not in ["accept", "decline"]:
            messages.error(request, "Action non valide.")
            return redirect("event:event_detail", uid=event.uid)  # noqa

        invitation = self.get_invitation(token, action)
        if not invitation:
            return redirect("event:event_detail", uid=event.uid)  # noqa

        event = invitation.event

        if action == "accept":
            if not event.statut:
                messages.error(request, "Cet événement n'est plus actif.")
                return redirect("event:event_detail", uid=event.uid)

            if event.end_date < timezone.now():
                messages.error(request, "Cet événement est déjà terminé.")
                return redirect("event:event_detail", uid=event.uid)

            if not event.verifier_disponibilite(invitation.ticket_type, 1):
                messages.error(
                    request, "Désolé, il n'y a plus de places disponibles pour cet événement."
                )
                return redirect("event:event_detail", uid=event.uid)

            if invitation.accept_invitation():
                messages.success(
                    request,
                    "Votre invitation a été acceptée. Vous recevrez votre ticket par email"
                    " sous peu.",
                )
            else:
                messages.error(request, "Une erreur s'est produite. Veuillez réessayer plus tard.")
        else:  # decline
            if invitation.decline_invitation():
                messages.info(
                    request, "Vous avez décliné l'invitation. Merci de nous avoir informés."
                )
            else:
                messages.error(request, "Une erreur s'est produite. Veuillez réessayer plus tard.")

        return redirect("event:event_detail", uid=event.uid)
