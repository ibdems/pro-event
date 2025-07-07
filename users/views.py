import logging
import uuid
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import (
    LoginView,
    PasswordResetCompleteView,
    PasswordResetConfirmView,
    PasswordResetDoneView,
    PasswordResetView,
)
from django.db import transaction
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.http import urlsafe_base64_decode
from django.views import View
from django.views.generic import CreateView

from users.models import User

from .forms import (
    CustomCreateUserForm,
    CustomLoginForm,
    CustomPasswordResetForm,
    CustomSetPasswordForm,
)
from .utils.send_emails import send_mail_activation, send_mail_reset_password

logger = logging.getLogger(__name__)


class CustomLoginView(LoginView):
    form_class = CustomLoginForm
    template_name = "accounts/sign-in.html"

    def form_valid(self, form):
        user = form.cleaned_data.get("user")
        if user is None:
            return self.form_invalid(form)

        # Connecter l'utilisateur
        login(self.request, user)

        # Rediriger vers la page de succès
        return redirect(self.get_success_url())

    def get_success_url(self):
        return self.request.GET.get("next", "/dashboard/")


class CustomUserCreationView(CreateView):
    template_name = "accounts/sign-up.html"
    form_class = CustomCreateUserForm
    success_url = reverse_lazy("login")

    def form_valid(self, form):
        try:
            with transaction.atomic():
                user = form.save(commit=False)
                user.is_active = False
                user.role = "organisateur"
                user.activation_token = uuid.uuid4().hex
                user.activation_token_created_at = timezone.now()
                user.save()
                user.refresh_from_db()
                logger.warning(
                    f"[DJANGO] Création: id={user.id}, email={user.email}, "
                    f"is_active={user.is_active}, last_login={user.last_login}"
                )
                transaction.on_commit(lambda: send_mail_activation(user.id))

            messages.success(
                self.request,
                "Votre compte a été créé avec succès. Un email d'activation vous a été envoyé. "
                "Veuillez vérifier votre boîte de réception (ainsi que vos spams)"
                " pour activer votre compte.",
            )
            return super().form_valid(form)
        except Exception as e:
            print(f"Erreur lors de la création du compte: {e}")
            messages.error(
                self.request,
                "Une erreur technique est survenue lors de"
                " la création de votre compte. Veuillez réessayer plus tard.",
            )
            return self.form_invalid(form)

    def form_invalid(self, form):
        print(f"Formulaire invalide: {form.errors}")
        return super().form_invalid(form)


class ActivationUserView(View):
    login_url = reverse_lazy("login")

    def get(self, request, uid, token):
        try:
            id = urlsafe_base64_decode(uid).decode("utf-8")
            user = User.objects.get(pk=id)
            logger.warning(
                f"[ACTIVATION] uid={uid}, token={token}, user.id={user.id}"
                f", user.email={user.email}, is_active={user.is_active}"
            )
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            print(f"Activation échouée: uid={uid}, token={token}")
            messages.error(request, "Le lien d'activation est invalide.")
            return render(request, "accounts/activation_invalid.html")

        # Vérification du token d'activation personnalisé
        if (
            user.activation_token == token
            and user.activation_token_created_at
            and timezone.now() - user.activation_token_created_at <= timedelta(hours=24)
        ):
            if user.is_active:
                messages.info(request, "Votre compte est déjà activé. Vous pouvez vous connecter.")
            else:
                user.is_active = True
                user.activation_token = None
                user.activation_token_created_at = None
                user.save()
                messages.success(
                    request,
                    "Votre compte a été activé avec succès. Vous pouvez maintenant vous connecter.",
                )
            return redirect(self.login_url)

        messages.error(request, "Le lien d'activation a expiré ou est invalide.")
        return render(request, "accounts/activation_invalid.html")


class CustomPasswordResetView(PasswordResetView):
    template_name = "accounts/password_reset.html"
    success_url = reverse_lazy("password_reset_done")
    email_template_name = "accounts/password_reset_email.txt"
    html_email_template_name = "accounts/password_reset_email.html"
    form_class = CustomPasswordResetForm

    def form_valid(self, form):
        """
        Surcharge complète de la méthode form_valid pour éviter l'envoi synchrone d'email
        """
        # Récupérer l'email et chercher l'utilisateur correspondant
        email = form.cleaned_data["email"]

        try:
            user = User.objects.get(email=email)

            # Lancer la tâche Celery d'envoi d'email
            task_id = send_mail_reset_password(user)
            print(f"Tâche d'envoi d'email de réinitialisation lancée avec ID: {task_id}")

            # Message de succès
            messages.success(
                self.request,
                "Vous allez recevoir un email de réinitialisation dans quelques instants. "
                "Veuillez consulter votre boîte mail (et vos spams).",
            )

            # Redirection vers la page de confirmation
            return redirect(self.success_url)

        except User.DoesNotExist:
            # Si l'utilisateur n'existe pas, on affiche un message
            messages.error(self.request, "Aucun compte n'est associé à cet email.")
            return self.form_invalid(form)
        except Exception as e:
            # En cas d'erreur, on log et on informe l'utilisateur
            print(f"Erreur lors de la réinitialisation du mot de passe: {e}")
            messages.error(
                self.request,
                "Une erreur est survenue lors de l'envoi de l'email de réinitialisation.",
            )
            return self.form_invalid(form)


class CustomPasswordResetDoneView(PasswordResetDoneView):
    template_name = "accounts/password_reset_done.html"


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = "accounts/password_reset_confirm.html"
    success_url = reverse_lazy("password_reset_complete")
    form_class = CustomSetPasswordForm

    def form_valid(self, form):
        messages.success(
            self.request,
            "Votre mot de passe a été modifié avec succès. Vous pouvez maintenant vous connecter.",
        )
        return super().form_valid(form)


class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = "accounts/password_reset_complete.html"


@login_required
def lock(request):
    """
    Vue pour gérer la page de verrouillage.
    """
    if request.method == "POST":
        password = request.POST.get("password")
        user = authenticate(request, username=request.user.email, password=password)
        if user:
            # Si l'utilisateur est authentifié, déverrouiller la session
            login(request, user)
            request.session["locked"] = False
            request.session["last_activity"] = timezone.now().timestamp()
            return redirect("dashboard:home")  # Redirection après succès
        else:
            return render(
                request,
                "accounts/locked.html",
                {
                    "error": "Mot de passe incorrect",
                    "user": request.user,
                },
            )

    # Marquer la session comme verrouillée par défaut
    request.session["locked"] = True
    return render(request, "accounts/locked.html", {"user": request.user})


def logout_view(request):
    logout(request)
    return redirect("/")
