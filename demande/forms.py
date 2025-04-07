from django import forms

from demande.models import AnonymousUser, Demande, Service, ServiceHotesse
from users.models import User


class AnonymousUserForms(forms.ModelForm):
    class Meta:
        model = AnonymousUser
        fields = ("first_name", "last_name", "email", "contact")

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if not email:
            raise forms.ValidationError("L'email est requis.")
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Cet email a deja un compte. Connectez-vous.")
        return email


class ServiceHotesseForms(forms.ModelForm):
    class Meta:
        model = ServiceHotesse
        fields = ("number_hotesse", "start_date_service", "end_date_service", "besoin")


class DemandeForms(forms.ModelForm):
    service = forms.ModelMultipleChoiceField(
        queryset=Service.objects.all(),
        widget=forms.CheckboxSelectMultiple(),
    )

    class Meta:
        model = Demande
        fields = ("service", "event", "ticket", "anonymous_user", "service_hotesse", "user")
