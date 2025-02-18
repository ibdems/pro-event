from django import forms

from demande.models import AnonymousUser, Demande, Service, ServiceHotesse


class AnonymousUserForms(forms.ModelForm):
    class Meta:
        model = AnonymousUser
        fields = ("first_name", "last_name", "email", "contact")


class ServiceHotesseForms(forms.ModelForm):
    class Meta:
        model = ServiceHotesse
        fields = ("number_hotesse", "start_date", "end_date", "besoin")


class DemandeForms(forms.ModelForm):
    service = forms.ModelMultipleChoiceField(
        queryset=Service.objects.all(),
        widget=forms.CheckboxSelectMultiple(),
    )

    class Meta:
        model = Demande
        fields = ("service", "event", "ticket", "anonymous_user", "service_hotesse", "user")
