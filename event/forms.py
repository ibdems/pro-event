from django import forms
from django.contrib.admin import widgets

from .models import Category, Contact, Event, Partner, Ticket


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


class TicketForms(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = (
            "email_reception",
            "telephone_payement",
            "telephone_reception",
        )


class ContactForm(forms.ModelForm):
    class Meta:
        model = Contact
        fields = "__all__"
