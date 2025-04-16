from django import forms
from django_filters import CharFilter, ChoiceFilter, FilterSet, ModelChoiceFilter

from .models import Category, Event, InfoTicket


class EventFilter(FilterSet):

    category = ModelChoiceFilter(
        queryset=Category.objects.all(),
        empty_label="Trier par catégorie",
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    title = CharFilter(
        field_name="title",
        lookup_expr="icontains",
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Rechercher par titre"}
        ),
    )
    type_access = ChoiceFilter(
        field_name="infoticket_event__type_access",
        choices=InfoTicket._meta.get_field("type_access").choices,
        empty_label="Trier par type d'accès",
        widget=forms.Select(attrs={"class": "form-control"}),
    )

    class Meta:
        model = Event
        fields = ["category", "title", "type_access"]
