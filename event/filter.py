from django import forms
from django_filters import CharFilter, ChoiceFilter, FilterSet, ModelChoiceFilter

from .models import Category, Event


class EventFilter(FilterSet):
    category = ModelChoiceFilter(
        queryset=Category.objects.all(),
        widget=forms.Select(
            attrs={"class": "form-control", "placeholder": "Filtrer par categorie"}
        ),
    )
    title = CharFilter(
        field_name="title",
        lookup_expr="icontains",
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Rechercher par titre"}
        ),
    )
    type_access = ChoiceFilter(
        field_name="type_access",
        choices=Event._meta.get_field("type_access").choices,
        widget=forms.Select(
            attrs={"class": "form-control", "placeholder": "Filtrer par type d'accès"}
        ),
    )

    class Meta:
        model = Event
        fields = ["category", "title", "type_access"]
