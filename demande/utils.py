import random
import string

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from users.models import User


def generate_password(length=10):
    """Génère un mot de passe aléatoire de la longueur spécifiée"""
    characters = string.ascii_letters + string.digits + "!@#$%^&*()"
    return "".join(random.choice(characters) for i in range(length))


def create_user_from_anonymous_user(anonymous_user):
    """Crée un compte utilisateur à partir d'un utilisateur anonyme"""
    password = generate_password()

    # Vérifier si l'utilisateur existe déjà
    if User.objects.filter(email=anonymous_user.email).exists():
        user = User.objects.get(email=anonymous_user.email)
        password = None  # Pas besoin de mot de passe pour un utilisateur existant
    else:
        # Créer un nouvel utilisateur
        user = User.objects.create_user(
            email=anonymous_user.email,
            password=password,
            first_name=anonymous_user.first_name,
            last_name=anonymous_user.last_name,
            contact=anonymous_user.contact,
        )

    return user, password


def send_demande_accepted_email(demande, password=None):
    """Envoie un email de notification d'acceptation de demande"""
    # Déterminer le destinataire (utilisateur anonyme ou utilisateur enregistré)
    if demande.anonymous_user:
        recipient_email = demande.anonymous_user.email
        recipient_name = f"{demande.anonymous_user.first_name} {demande.anonymous_user.last_name}"
    else:
        recipient_email = demande.user.email if demande.user else "no-reply@proevent.com"

        # Approche défensive pour obtenir le nom complet
        try:
            if demande.user and hasattr(demande.user, "get_full_name"):
                recipient_name = demande.user.get_full_name() or demande.user.email
            elif demande.user:
                # Fallback si get_full_name n'est pas disponible
                if demande.user.first_name and demande.user.last_name:
                    recipient_name = f"{demande.user.first_name} {demande.user.last_name}"
                else:
                    recipient_name = demande.user.email
            else:
                recipient_name = "Utilisateur"
        except Exception:
            # En cas d'erreur, utiliser une valeur par défaut
            recipient_name = "Utilisateur de ProEvent"

    # Construire le contexte pour le template d'email
    context = {
        "name": recipient_name,
        "demande": demande,
        "services": demande.service.all(),
        "has_password": password is not None,
        "password": password,
        "login_url": settings.LOGIN_URL,
    }

    # Rendre les templates HTML et texte
    html_message = render_to_string("event/emails/demande_accepted.html", context)
    plain_message = strip_tags(html_message)

    # Envoyer l'email
    send_mail(
        subject="Votre demande a été acceptée - ProEvent",
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[recipient_email],
        html_message=html_message,
    )


def send_demande_rejected_email(demande):
    """Envoie un email de notification de rejet de demande"""
    # Déterminer le destinataire (utilisateur anonyme ou utilisateur enregistré)
    if demande.anonymous_user:
        recipient_email = demande.anonymous_user.email
        recipient_name = f"{demande.anonymous_user.first_name} {demande.anonymous_user.last_name}"
    else:
        recipient_email = demande.user.email if demande.user else "no-reply@proevent.com"

        # Approche défensive pour obtenir le nom complet
        try:
            if demande.user and hasattr(demande.user, "get_full_name"):
                recipient_name = demande.user.get_full_name() or demande.user.email
            elif demande.user:
                # Fallback si get_full_name n'est pas disponible
                if demande.user.first_name and demande.user.last_name:
                    recipient_name = f"{demande.user.first_name} {demande.user.last_name}"
                else:
                    recipient_name = demande.user.email
            else:
                recipient_name = "Utilisateur"
        except Exception:
            # En cas d'erreur, utiliser une valeur par défaut
            recipient_name = "Utilisateur de ProEvent"

    # Construire le contexte pour le template d'email
    context = {
        "name": recipient_name,
        "demande": demande,
        "services": demande.service.all(),
    }

    # Rendre les templates HTML et texte
    html_message = render_to_string("event/emails/demande_rejected.html", context)
    plain_message = strip_tags(html_message)

    # Envoyer l'email
    send_mail(
        subject="Concernant votre demande - ProEvent",
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[recipient_email],
        html_message=html_message,
    )
