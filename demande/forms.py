from django import forms
from django_recaptcha.fields import ReCaptchaField
from django_recaptcha.widgets import ReCaptchaV3

from demande.models import AnonymousUser, Demande, Service, ServiceHotesse


class AnonymousUserForms(forms.ModelForm):
    captcha = ReCaptchaField(widget=ReCaptchaV3(action="demande"))

    class Meta:
        model = AnonymousUser
        fields = ("first_name", "last_name", "email", "contact", "captcha")

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if not email:
            raise forms.ValidationError("L'email est requis.")

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
