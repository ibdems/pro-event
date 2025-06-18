import random
import string

from celery import shared_task
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from users.models import User


@shared_task(name="users.send_activation_email")
def send_activation_email(user_id, email, first_name, last_name):
    """
    Tâche Celery pour l'envoi d'un email d'activation de compte
    """
    from users.models import User

    try:
        user = User.objects.get(id=user_id)

        # Génération des tokens
        uid = urlsafe_base64_encode(force_bytes(user.id))
        token = default_token_generator.make_token(user)

        # Contexte pour le template
        context = {"user": user, "uid": uid, "token": token, "domain": settings.DOMAIN_URL}

        # Rendu du template HTML
        html_message = render_to_string("registration/activation_mail.html", context)

        # Version texte simple
        plain_message = f"""
Bonjour {first_name} {last_name or ''} ou {email},

Merci de vous être inscrit sur ProEvent.
Pour activer votre compte, veuillez cliquer sur le lien ci-dessous :

http://{settings.DOMAIN_URL}/accounts/activation/{uid}/{token}/

Ce lien est valable pendant 24 heures.

Cordialement,
L'équipe ProEvent
        """

        # Récupérer l'email expéditeur depuis les paramètres
        from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@proevent.com")

        # Envoi de l'email avec version HTML et texte
        send_mail(
            subject="Activation de votre compte",
            message=plain_message,
            from_email=from_email,
            recipient_list=[email],
            fail_silently=False,
            html_message=html_message,
        )

        return f"Email d'activation envoyé à {email} (uid={uid}, token={token})"
    except User.DoesNotExist:
        return f"Utilisateur {user_id} introuvable"
    except Exception as e:
        return f"Erreur lors de l'envoi de l'email d'activation: {str(e)}"


@shared_task(name="users.send_password_reset_email")
def send_password_reset_email(user_id, email, first_name, last_name):
    """
    Tâche Celery pour l'envoi d'un email de réinitialisation de mot de passe
    """
    from users.models import User

    try:
        user = User.objects.get(id=user_id)

        # Génération des tokens
        uid = urlsafe_base64_encode(force_bytes(user.id))
        token = default_token_generator.make_token(user)

        # Contexte pour le template
        context = {"user": user, "uid": uid, "token": token, "domain": settings.DOMAIN_URL}

        # Rendu du template HTML
        html_message = render_to_string("registration/reset_password.html", context)

        # Version texte simple
        plain_message = f"""
Bonjour {first_name} {last_name or ''} ou {email},

Vous avez demandé la réinitialisation de votre mot de passe ProEvent.
Pour définir un nouveau mot de passe, veuillez cliquer sur le lien ci-dessous :

http://{settings.DOMAIN_URL}/accounts/reset/{uid}/{token}/

Ce lien est valable pendant 24 heures.

Si vous n'avez pas demandé cette réinitialisation, veuillez ignorer cet email.

Cordialement,
L'équipe ProEvent
        """

        # Récupérer l'email expéditeur depuis les paramètres
        from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@proevent.com")

        # Envoi de l'email avec version HTML et texte
        send_mail(
            subject="Réinitialisation de votre mot de passe",
            message=plain_message,
            from_email=from_email,
            recipient_list=[email],
            fail_silently=False,
            html_message=html_message,
        )

        return (
            f"Email de réinitialisation de mot de passe envoyé à {email} (uid={uid}, token={token})"
        )
    except User.DoesNotExist:
        return f"Utilisateur {user_id} introuvable"
    except Exception as e:
        return f"Erreur lors de l'envoi de l'email de réinitialisation: {str(e)}"


@shared_task(name="users.send_welcome_password_email")
def send_welcome_password_email(user_id, email, password, is_new_account=True):
    """
    Tâche Celery pour l'envoi d'un email avec mot de passe
    """
    from users.models import User

    try:
        user = User.objects.get(id=user_id)

        if is_new_account:
            subject = "Bienvenue sur ProEvent - Vos informations de connexion"
            template = "registration/welcome_password.html"
        else:
            subject = "Réinitialisation de votre mot de passe ProEvent"
            template = "registration/password_reset_notification.html"

        context = {
            "user": user,
            "password": password,
            "login_url": settings.LOGIN_URL if hasattr(settings, "LOGIN_URL") else "/login/",
            "domain": settings.DOMAIN_URL if hasattr(settings, "DOMAIN_URL") else "proeventgn.com",
        }

        html_message = render_to_string(template, context)

        # Version texte simple adaptée au type d'email
        if is_new_account:
            plain_message = f"""
Bonjour {user.get_full_name() or user.email},

Bienvenue sur ProEvent ! Votre compte a été créé avec succès.

Voici vos informations de connexion :
Email: {email}
Mot de passe: {password}

Pour vous connecter, rendez-vous sur http://{settings.DOMAIN_URL}{settings.LOGIN_URL}

Cordialement,
L'équipe ProEvent
            """
        else:
            plain_message = f"""
Bonjour {user.get_full_name() or user.email},

Votre mot de passe ProEvent a été réinitialisé.

Voici votre nouveau mot de passe : {password}

Pour vous connecter, rendez-vous sur http://{settings.DOMAIN_URL}{settings.LOGIN_URL}

Cordialement,
L'équipe ProEvent
            """

        # Récupérer l'email expéditeur depuis les paramètres
        from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@proevent.com")

        # Envoi de l'email avec version HTML et texte
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=from_email,
            recipient_list=[email],
            fail_silently=False,
            html_message=html_message,
        )

        return f"Email avec mot de passe envoyé à {email}"
    except User.DoesNotExist:
        return f"Utilisateur {user_id} introuvable"
    except Exception as e:
        return f"Erreur lors de l'envoi de l'email avec mot de passe: {str(e)}"


@shared_task(name="users.generate_and_send_new_password")
def generate_and_send_new_password(user_id, is_new_account=False):

    try:
        user = User.objects.get(id=user_id)

        # Générer un mot de passe aléatoire
        chars = string.ascii_letters + string.digits + string.punctuation
        password = "".join(random.choice(chars) for _ in range(12))

        # Définir le nouveau mot de passe
        user.set_password(password)
        user.save()

        # Déterminer le template et le sujet en fonction du contexte
        if is_new_account:
            subject = "Bienvenue sur ProEvent - Vos informations de connexion"
            template = "registration/welcome_password.html"
        else:
            subject = "Réinitialisation de votre mot de passe ProEvent"
            template = "registration/password_reset_notification.html"

        # Contexte pour le template
        context = {
            "user": user,
            "password": password,
            "login_url": settings.LOGIN_URL if hasattr(settings, "LOGIN_URL") else "/login/",
            "domain": settings.DOMAIN_URL if hasattr(settings, "DOMAIN_URL") else "proeventgn.com",
        }

        # Rendu du template HTML
        html_message = render_to_string(template, context)

        # Version texte simple adaptée au type d'email
        if is_new_account:
            plain_message = f"""
Bonjour {user.get_full_name() or user.email},

Bienvenue sur ProEvent ! Votre compte a été créé avec succès.

Voici vos informations de connexion :
Email: {user.email}
Mot de passe: {password}

Pour vous connecter, rendez-vous sur http://{settings.DOMAIN_URL}{settings.LOGIN_URL}

Cordialement,
L'équipe ProEvent
            """
        else:
            plain_message = f"""
Bonjour {user.get_full_name() or user.email},

Votre mot de passe ProEvent a été réinitialisé.

Voici votre nouveau mot de passe : {password}

Pour vous connecter, rendez-vous sur http://{settings.DOMAIN_URL}{settings.LOGIN_URL}

Cordialement,
L'équipe ProEvent
            """

        # Récupérer l'email expéditeur depuis les paramètres
        from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@proevent.com")

        # Envoi de l'email avec version HTML et texte
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=from_email,
            recipient_list=[user.email],
            fail_silently=False,
            html_message=html_message,
        )

        return f"Nouveau mot de passe généré et envoyé à {user.email}"
    except User.DoesNotExist:
        return f"Utilisateur {user_id} introuvable"
    except Exception as e:
        return f"Erreur lors de la génération et de l'envoi du mot de passe: {str(e)}"
