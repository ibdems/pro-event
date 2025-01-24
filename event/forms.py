from django import forms
from django.contrib.admin import widgets
from django.forms import ValidationError

from .models import Category, Contact, Event, Partner, Payement


class CategoryForms(forms.ModelForm):
    class Meta:
        model = Category
        fields = ("name",)


class PartnerForms(forms.ModelForm):
    class Meta:
        model = Partner
        fields = ("name", "logo", "description", "partnership_type")


class EventForms(forms.ModelForm):
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(), empty_label="Choisir une catégorie"
    )
    partner = forms.ModelMultipleChoiceField(
        queryset=Partner.objects.all(), required=False, widget=forms.CheckboxSelectMultiple
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["start_date"].input_formats = ["%Y-%m-%dT%H:%M"]
        self.fields["end_date"].input_formats = ["%Y-%m-%dT%H:%M"]

    class Meta:
        model = Event
        fields = (
            "category",
            "title",
            "description",
            "start_date",
            "end_date",
            "location",
            "normal_capacity",
            "vip_capacity",
            "vvip_capacity",
            "prix_normal",
            "prix_vip",
            "prix_vvip",
            "image",
            "type_event",
            "partner",
            "type_access",
        )
        widgets = {
            "start_date": forms.DateTimeInput(
                format="%Y-%m-%dT%H:%M", attrs={"type": "datetime-local", "class": "form-control"}
            ),
            "end_date": forms.DateTimeInput(
                format="%Y-%m-%dT%H:%M", attrs={"type": "datetime-local", "class": "form-control"}
            ),
        }


class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = "__all__"
        widgets = {
            "start_date": widgets.AdminSplitDateTime(),
            "end_date": widgets.AdminSplitDateTime(),
        }


class ContactForm(forms.ModelForm):
    class Meta:
        model = Contact
        fields = "__all__"


class PayementForm(forms.ModelForm):
    email_reception2 = forms.EmailField(required=False)
    telephone_reception2 = forms.CharField(max_length=20, required=False)
    quantity_normal = forms.IntegerField(min_value=0, required=False)
    quantity_vip = forms.IntegerField(min_value=0, required=False)
    quantity_vvip = forms.IntegerField(min_value=0, required=False)

    class Meta:
        model = Payement
        fields = (
            "nom_complet",
            "email_reception",
            "telephone_payement",
            "telephone_reception",
            "payment_method",
            "statut_payement",
        )

    def clean(self):
        cleaned_data = super().clean()
        email_reception = cleaned_data.get("email_reception")
        email_reception2 = cleaned_data.get("email_reception2")
        telephone_reception = cleaned_data.get("telephone_reception")
        telephone_reception2 = cleaned_data.get("telephone_reception2")

        # Vérifier si au moins une méthode de contact est fournie
        if not email_reception and not telephone_reception:
            raise ValidationError(
                """Vous devez fournir un email ou un numéro de téléphone pour
                  la réception de votre ticket."""
            )

        # Vérification des emails
        if email_reception and email_reception != email_reception2:
            raise ValidationError("Les deux adresses email doivent être identiques.")

        # Vérification des numéros de téléphone
        if telephone_reception and telephone_reception != telephone_reception2:
            raise ValidationError("Les deux numéros de téléphone doivent être identiques.")

        return cleaned_data
