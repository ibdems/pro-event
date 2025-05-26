from django import forms

from .models import Category, Contact, Event, InfoTicket, Partner, Payement


class CategoryForms(forms.ModelForm):
    class Meta:
        model = Category
        fields = ("name",)


class PartnerForms(forms.ModelForm):
    class Meta:
        model = Partner
        fields = ("name", "logo", "description", "partnership_type", "is_platform_partner")


class EventForms(forms.ModelForm):
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        empty_label="Choisir une catégorie",
        widget=forms.Select(attrs={"class": "form-control form-select"}),
    )
    partner = forms.ModelMultipleChoiceField(
        queryset=Partner.objects.all(),
        required=False,
        widget=forms.SelectMultiple(attrs={"class": "form-control form-select", "size": "3"}),
    )
    statut = forms.BooleanField(
        required=False, widget=forms.CheckboxInput(attrs={"class": "form-check-input"})
    )
    type_event = forms.ChoiceField(
        choices=Event.type_choices, widget=forms.Select(attrs={"class": "form-control form-select"})
    )

    class Meta:
        model = Event
        fields = (
            "title",
            "category",
            "description",
            "type_event",
            "start_date",
            "end_date",
            "location",
            "image",
            "partner",
            "statut",
        )
        widgets = {
            "title": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Titre de l'événement"}
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Description détaillée de l'événement",
                }
            ),
            "location": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Lieu de l'événement"}
            ),
            "image": forms.FileInput(attrs={"class": "form-control"}),
            "start_date": forms.DateTimeInput(
                format="%Y-%m-%dT%H:%M",
                attrs={
                    "type": "datetime-local",
                    "class": "form-control",
                    "placeholder": "Date et heure de début",
                    "step": "900",  # Par pas de 15 minutes (900 secondes)
                },
            ),
            "end_date": forms.DateTimeInput(
                format="%Y-%m-%dT%H:%M",
                attrs={
                    "type": "datetime-local",
                    "class": "form-control",
                    "placeholder": "Date et heure de fin",
                    "step": "900",  # Par pas de 15 minutes (900 secondes)
                },
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["start_date"].input_formats = ("%Y-%m-%dT%H:%M",)
        self.fields["end_date"].input_formats = ("%Y-%m-%dT%H:%M",)

        # Rendre les champs obligatoires plus évidents
        required_fields = [
            "title",
            "category",
            "description",
            "type_event",
            "start_date",
            "end_date",
            "location",
        ]
        for field_name in required_fields:
            if field_name in self.fields:
                self.fields[field_name].widget.attrs["required"] = "required"


class TicketForms(forms.ModelForm):
    type_access = forms.ChoiceField(
        choices=(("gratuit", "Gratuit"), ("payant", "Payant")),
        widget=forms.Select(attrs={"class": "form-control form-select"}),
    )

    class Meta:
        model = InfoTicket
        fields = (
            "type_access",
            "normal_capacity",
            "prix_normal",
            "vip_capacity",
            "prix_vip",
            "vvip_capacity",
            "prix_vvip",
        )
        widgets = {
            "normal_capacity": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": "1",
                    "placeholder": "Capacité pour les tickets normaux",
                }
            ),
            "vip_capacity": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": "0",
                    "placeholder": "Capacité pour les tickets VIP",
                }
            ),
            "vvip_capacity": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": "0",
                    "placeholder": "Capacité pour les tickets VVIP",
                }
            ),
            "prix_normal": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": "0",
                    "placeholder": "Prix en FG pour les tickets normaux",
                }
            ),
            "prix_vip": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": "0",
                    "placeholder": "Prix en FG pour les tickets VIP",
                }
            ),
            "prix_vvip": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": "0",
                    "placeholder": "Prix en FG pour les tickets VVIP",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Rendre les champs obligatoires plus évidents
        required_fields = ["type_access", "normal_capacity"]
        for field_name in required_fields:
            if field_name in self.fields:
                self.fields[field_name].widget.attrs["required"] = "required"

        # Ajouter des descriptions aux champs
        self.fields["normal_capacity"].help_text = "Nombre total de tickets normaux disponibles"
        self.fields["vip_capacity"].help_text = (
            "Nombre total de tickets VIP disponibles (0 pour aucun)"
        )
        self.fields["vvip_capacity"].help_text = (
            "Nombre total de tickets VVIP disponibles (0 pour aucun)"
        )
        self.fields["prix_normal"].help_text = "Prix unitaire en Francs Guinéens (FG)"
        self.fields["prix_vip"].help_text = "Prix unitaire en Francs Guinéens (FG)"
        self.fields["prix_vvip"].help_text = "Prix unitaire en Francs Guinéens (FG)"


class ContactForm(forms.ModelForm):
    class Meta:
        model = Contact
        fields = ("name", "email", "subject", "message")
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Votre nom"}),
            "email": forms.EmailInput(
                attrs={"class": "form-control", "placeholder": "Votre adresse email"}
            ),
            "subject": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Le sujet de votre message"}
            ),
            "message": forms.Textarea(
                attrs={"class": "form-control", "rows": 5, "placeholder": "Votre message"}
            ),
        }


class PayementForm(forms.ModelForm):
    CONTACT_CHOICES = [
        ("email", "Email"),
        ("phone", "WhatsApp"),
    ]

    nom_complet = forms.CharField(max_length=150, required=True)
    email_reception = forms.EmailField(required=False)
    email_reception2 = forms.EmailField(required=False)
    telephone_reception = forms.CharField(max_length=20, required=False)
    telephone_reception2 = forms.CharField(max_length=20, required=False)
    contact_method = forms.ChoiceField(choices=CONTACT_CHOICES, required=True, initial="email")
    quantity_normal = forms.IntegerField(min_value=0, required=False)
    quantity_vip = forms.IntegerField(min_value=0, required=False)
    quantity_vvip = forms.IntegerField(min_value=0, required=False)

    class Meta:
        model = Payement
        fields = (
            "nom_complet",
            "email_reception",
            "telephone_reception",
            "payment_method",
        )

    def clean(self):
        cleaned_data = super().clean()
        email_reception = cleaned_data.get("email_reception")
        email_reception2 = cleaned_data.get("email_reception2")
        telephone_reception = cleaned_data.get("telephone_reception")
        telephone_reception2 = cleaned_data.get("telephone_reception2")
        contact_method = cleaned_data.get("contact_method")

        # Vérifier la méthode de contact
        if contact_method == "email":
            if not email_reception:
                raise forms.ValidationError(
                    "L'adresse email est requise pour recevoir les tickets par email"
                )

            # Vérification des emails
            if email_reception and email_reception != email_reception2:
                raise forms.ValidationError("Les deux adresses email doivent être identiques.")

        elif contact_method == "phone":
            if not telephone_reception:
                raise forms.ValidationError(
                    "Le numéro WhatsApp est requis pour recevoir les tickets par WhatsApp"
                )

            # Vérification des numéros WhatsApp
            if telephone_reception and telephone_reception != telephone_reception2:
                raise forms.ValidationError("Les deux numéros WhatsApp doivent être identiques.")

            if telephone_reception and not telephone_reception.isdigit():
                raise forms.ValidationError(
                    "Le numéro WhatsApp doit contenir uniquement des chiffres"
                )

        return cleaned_data
