import random
import string
import uuid

from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import (
    AuthenticationForm,
    PasswordResetForm,
    SetPasswordForm,
    UserCreationForm,
)
from django.core.exceptions import ValidationError
from django.utils import timezone
from django_recaptcha.fields import ReCaptchaField
from django_recaptcha.widgets import ReCaptchaV3

from users.models import User

from .utils.send_emails import send_mail_activation, send_password_email


class CustomLoginForm(AuthenticationForm):
    username = forms.EmailField(
        label=("Votre email"),
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Email"}),
    )
    password = forms.CharField(
        label=("Votre mot de passe"),
        strip=False,
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Mot de passe"}),
    )
    captcha = ReCaptchaField(widget=ReCaptchaV3(action="login"))

    def clean(self) -> dict:
        username = self.cleaned_data.get("username")
        password = self.cleaned_data.get("password")

        # Vérifier si l'utilisateur existe d'abord
        try:
            user = User.objects.get(email=username)

            # Vérifier si le compte est actif
            if not user.is_active:
                # Générer un nouveau token d'activation et le stocker
                user.activation_token = uuid.uuid4().hex
                user.activation_token_created_at = timezone.now()
                user.save(update_fields=["activation_token", "activation_token_created_at"])
                # Renvoyer l'email d'activation en arrière-plan
                task_id = send_mail_activation(user.id)
                print(f"Tâche d'envoi d'email d'activation lancée avec ID: {task_id}")

                # Message plus descriptif pour aider l'utilisateur
                raise ValidationError(
                    "Votre compte n'est pas encore activé. Un nouvel"
                    " email d'activation vient de vous être envoyé. "
                    "Veuillez vérifier votre boîte de réception (et vos spams) pour"
                    " activer votre compte."
                )

            # Authentifier l'utilisateur avec le mot de passe fourni
            auth_user = authenticate(email=username, password=password)

            if auth_user is None:
                raise ValidationError("Email ou mot de passe incorrect.")

            # Stocker l'utilisateur pour une utilisation ultérieure
            self.cleaned_data["user"] = auth_user
            return self.cleaned_data

        except User.DoesNotExist:
            raise ValidationError("Aucun compte n'existe avec cette adresse email.")


class CustomPasswordResetForm(PasswordResetForm):
    """Formulaire personnalisé pour la réinitialisation du mot de passe"""

    email = forms.EmailField(
        label="Adresse email",
        max_length=254,
        widget=forms.EmailInput(
            attrs={"class": "form-control", "placeholder": "Entrez votre adresse email"}
        ),
    )


class CustomSetPasswordForm(SetPasswordForm):
    """Formulaire personnalisé pour définir un nouveau mot de passe"""

    new_password1 = forms.CharField(
        label="Nouveau mot de passe",
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": "Nouveau mot de passe"}
        ),
        strip=False,
    )
    new_password2 = forms.CharField(
        label="Confirmer le nouveau mot de passe",
        strip=False,
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": "Confirmer le nouveau mot de passe"}
        ),
    )


class CustomCreateUserForm(UserCreationForm):
    password1 = forms.CharField(
        label="Mot de passe",
        strip=False,
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": "Votre mot de passe"}
        ),
    )
    password2 = forms.CharField(
        label="Confirmation",
        strip=False,
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": "Confirmez votre mot de passe"}
        ),
    )
    captcha = ReCaptchaField(widget=ReCaptchaV3(action="signup"))

    class Meta:
        model = User
        fields = (
            "email",
            "first_name",
            "last_name",
            "adresse",
            "contact",
            "password1",
            "password2",
            "captcha",
        )
        widgets = {
            "first_name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Votre Prénom"}
            ),
            "last_name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Votre nom"}
            ),
            "email": forms.EmailInput(
                attrs={"class": "form-control", "placeholder": "example@company.com"}
            ),
        }

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if User.objects.filter(email=email).exists():
            raise ValidationError("Cette adresse email existe deja.")
        return email


class AdminUserCreationForm(forms.ModelForm):
    """
    Formulaire de création d'utilisateur pour les administrateurs.
    N'utilise pas de username et génère un mot de passe aléatoire
    """

    email = forms.EmailField(
        label="Email",
        required=True,
        widget=forms.EmailInput(
            attrs={"class": "form-control", "placeholder": "exemple@domaine.com"}
        ),
    )

    first_name = forms.CharField(
        label="Prénom",
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Prénom"}),
    )

    last_name = forms.CharField(
        label="Nom",
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Nom"}),
    )

    adresse = forms.CharField(
        label="Adresse",
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Adresse"}),
    )

    contact = forms.CharField(
        label="Téléphone",
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Téléphone"}),
    )

    role = forms.ChoiceField(
        label="Rôle",
        choices=User.role_choices,
        required=False,
        widget=forms.Select(attrs={"class": "form-control form-select"}),
    )

    is_active = forms.BooleanField(
        label="Utilisateur actif",
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )

    is_staff = forms.BooleanField(
        label="Organisateur",
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )

    is_superuser = forms.BooleanField(
        label="Administrateur",
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )

    send_welcome_email = forms.BooleanField(
        label="Envoyer un email de bienvenue avec le mot de passe",
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )

    class Meta:
        model = User
        fields = (
            "email",
            "first_name",
            "last_name",
            "adresse",
            "contact",
            "role",
            "is_active",
            "is_staff",
            "is_superuser",
        )

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if User.objects.filter(email=email).exists():
            raise ValidationError("Un utilisateur avec cette adresse email existe déjà.")
        return email

    def generate_random_password(self, length=12):
        """Génère un mot de passe aléatoire"""
        chars = string.ascii_letters + string.digits + string.punctuation
        return "".join(random.choice(chars) for _ in range(length))

    def save(self, commit=True):
        user = super().save(commit=False)

        # Générer et définir un mot de passe aléatoire
        random_password = self.generate_random_password()
        user.set_password(random_password)

        if commit:
            user.save()

            # Envoyer un email avec le mot de passe si demandé (asynchrone)
            if self.cleaned_data.get("send_welcome_email"):
                task_id = send_password_email(user, random_password, is_new_account=True)
                print(f"Tâche d'envoi d'email de bienvenue lancée avec ID: {task_id}")

        # Stocker le mot de passe pour pouvoir l'afficher dans l'interface
        user.generated_password = random_password

        return user


class AdminUserChangeForm(forms.ModelForm):
    """
    Formulaire de modification d'utilisateur pour les administrateurs.
    Sans modification de mot de passe (qui sera géré séparément)
    """

    email = forms.EmailField(
        label="Email",
        required=True,
        widget=forms.EmailInput(
            attrs={"class": "form-control", "placeholder": "exemple@domaine.com"}
        ),
    )

    first_name = forms.CharField(
        label="Prénom",
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Prénom"}),
    )

    last_name = forms.CharField(
        label="Nom",
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Nom"}),
    )

    adresse = forms.CharField(
        label="Adresse",
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Adresse"}),
    )

    contact = forms.CharField(
        label="Téléphone",
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Téléphone"}),
    )

    role = forms.ChoiceField(
        label="Rôle",
        choices=User.role_choices,
        required=False,
        widget=forms.Select(attrs={"class": "form-control form-select"}),
    )

    is_active = forms.BooleanField(
        label="Utilisateur actif",
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )

    is_staff = forms.BooleanField(
        label="Organisateur",
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )

    is_superuser = forms.BooleanField(
        label="Administrateur",
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )

    reset_password = forms.BooleanField(
        label="Réinitialiser le mot de passe et envoyer par email",
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )

    class Meta:
        model = User
        fields = (
            "email",
            "first_name",
            "last_name",
            "adresse",
            "contact",
            "role",
            "is_active",
            "is_staff",
            "is_superuser",
        )

    def clean_email(self):
        email = self.cleaned_data.get("email")
        instance = getattr(self, "instance", None)

        if instance and instance.email != email and User.objects.filter(email=email).exists():
            raise ValidationError("Un utilisateur avec cette adresse email existe déjà.")

        return email

    def generate_random_password(self, length=12):
        """Génère un mot de passe aléatoire"""
        chars = string.ascii_letters + string.digits + string.punctuation
        return "".join(random.choice(chars) for _ in range(length))

    def save(self, commit=True):
        user = super().save(commit=False)

        if self.cleaned_data.get("reset_password"):
            # Générer et définir un mot de passe aléatoire
            random_password = self.generate_random_password()
            user.set_password(random_password)

            # Stocker le mot de passe pour pouvoir l'afficher dans l'interface
            user.generated_password = random_password

            # Sauvegarder l'utilisateur d'abord
            if commit:
                user.save()

                # Envoyer un email avec le nouveau mot de passe (asynchrone)
                task_id = send_password_email(user, random_password, is_new_account=False)
                print(f"Tâche d'envoi d'email avec mot de passe lancée avec ID: {task_id}")
        elif commit:
            user.save()

        return user
