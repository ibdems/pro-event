from django.core.mail import send_mail
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.template.loader import render_to_string
from django.conf import settings

def send_mail_activation(user):
    subject= "Activation de votre compte"
    uid = urlsafe_base64_encode(force_bytes(user.id))
    token = default_token_generator.make_token(user)
    message = render_to_string(
        'registration/activation_mail.html',
        {
            'user': user,
            'uid': uid,
            'token': token,
            'domain': settings.DOMAIN_URL
        }
    )
    send_mail(
        subject,message, 'reservation03@exemple.com', [user.email], fail_silently=False
    )

def send_mail_reset_password(user):
    subject= "Reinitialisation de votre mot de passe"
    uid = urlsafe_base64_encode(force_bytes(user.id))
    token = default_token_generator.make_token(user)
    message = render_to_string(
        'registration/reset_password.html',
        {
            'user': user,
            'uid': uid,
            'token': token,
            'domain': settings.DOMAIN_URL
        }
    )
    send_mail(
        subject,message, 'reservation03@exemple.com', [user.email], fail_silently=False
    )