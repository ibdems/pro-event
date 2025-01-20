from admin_volt.forms import LoginForm
from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import UserCreationForm, UsernameField
from django.core.exceptions import ValidationError

from users.models import User

from .utils.send_emails import send_mail_activation


class CustomLoginForm(LoginForm):
    username = UsernameField(
        label=("Votre email"),
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Email"}),
    )
    password = forms.CharField(
        label=("Votre mot de passe"),
        strip=False,
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Mot de passe"}),
    )

    def clean(self) -> dict:
        username = self.cleaned_data.get("username")
        password = self.cleaned_data.get("password")

        # Authentifier l'utilisateur
        user = authenticate(email=username, password=password)

        if user is None:
            raise ValidationError("Email ou mot de passe invalide")

        if not user.is_active:
            send_mail_activation(user)
            raise ValidationError(
                "Votre compte n'est pas actif. Consultez votre boîte mail pour l'activer."
            )

        # Stocker l'utilisateur pour une utilisation ultérieure
        self.cleaned_data["user"] = user
        return self.cleaned_data


class CustomCreateUserForm(UserCreationForm):
    class Meta:
        model = User
        fields = (
            "email",
            "first_name",
            "last_name",
            "adresse",
            "contact",
            "role",
            "password1",
            "password2",
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
