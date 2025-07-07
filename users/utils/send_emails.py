from django.core.mail import send_mail

from users.models import User
from users.tasks import (
    generate_and_send_new_password,
    send_password_reset_email,
    send_welcome_password_email,
)


def send_mail_activation(user_id):
    user = User.objects.get(id=user_id)
    activation_link = (
        f"http://{user.get_domain_url()}/accounts/activation/{user.id}/{user.activation_token}/"
    )
    subject = "Activation de votre compte"
    plain_message = f"""
Bonjour {user.get_full_name() or user.email},

Merci de vous être inscrit sur ProEvent.
Pour activer votre compte, veuillez cliquer sur le lien ci-dessous :

{activation_link}

Ce lien est valable pendant 24 heures.

Cordialement,
L'équipe ProEvent
    """
    from_email = getattr(
        user._meta.app_config.module.settings, "DEFAULT_FROM_EMAIL", "noreply@proevent.com"
    )
    # Envoi de l'email (version simplifiée)
    send_mail(
        subject=subject,
        message=plain_message,
        from_email=from_email,
        recipient_list=[user.email],
        fail_silently=False,
    )
    return f"Email d'activation envoyé à {user.email} (id={user.id}, token={user.activation_token})"


def send_mail_reset_password(user):
    task = send_password_reset_email.delay(
        user_id=user.id,
        email=user.email,
        first_name=user.first_name or "",
        last_name=user.last_name or "",
    )

    return task.id


def send_password_email(user, password, is_new_account=False):
    task = send_welcome_password_email.delay(
        user_id=user.id, email=user.email, password=password, is_new_account=is_new_account
    )

    return task.id


def generate_new_password_and_send(user, is_new_account=False):
    task = generate_and_send_new_password.delay(user_id=user.id, is_new_account=is_new_account)

    return task.id
