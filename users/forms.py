from typing import Any

from admin_volt.forms import LoginForm
from django import forms
from django.contrib.auth.forms import UserCreationForm, UsernameField
from django.contrib.auth.hashers import check_password
from django.core.exceptions import ValidationError

from users.models import User

from .utils.send_emails import send_mail_activation


class CustomLoginForm(LoginForm):
    username = UsernameField(
        label=("Votre email"),
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Email"}),
    )
    password = forms.CharField(
        label=("Votre mot de pass"),
        strip=False,
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Mot de pass"}),
    )

    def clean(self) -> dict[str, Any]:
        username = self.cleaned_data.get("username")
        password = self.cleaned_data.get("password")

        try:
            user = User.objects.get(email=username)
        except Exception:
            raise ValidationError("Email ou mot de pass invalid")

        if not user.is_active:
            send_mail_activation(user)
            raise ValidationError(
                "Votre compte n'est pas actif, consulter votre boite mail pour l'activer"
            )

        if not check_password(password, user.password):
            raise ValidationError("Email ou mot de pass invalid")

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
