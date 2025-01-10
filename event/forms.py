from django import forms

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
            "image",
            "type_event",
            "partner",
            "type_access",
        )
        widgets = {
            "start_date": forms.DateTimeInput(
                format="%Y-%m-%dT%H:%M", attrs={"type": "datetime-local"}
            ),
            "end_date": forms.DateTimeInput(
                format="%Y-%m-%dT%H:%M", attrs={"type": "datetime-local"}
            ),
        }


class TicketForms(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = (
            "email_reception",
            "telephone_payement",
            "telephone_reception",
            "prix_normal",
            "prix_vip",
            "prix_vvip",
        )


class ContactForm(forms.ModelForm):
    class Meta:
        model = Contact
        fields = "__all__"
