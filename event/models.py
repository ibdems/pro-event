import uuid
from io import BytesIO

import qrcode
from django.core.files import File
from django.db import models
from django.db.models import Count
from django.forms import ValidationError
from django.utils import timezone

from users.models import User


class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Catgorie"


class Partner(models.Model):
    partner_choices = (
        ("exclusive", "Exclusive"),
        ("sponsor", "Sponsor"),
        ("collaborator", "Collaborator"),
    )
    name = models.CharField(max_length=100)
    logo = models.ImageField(upload_to="partner_logo/", blank=True, null=True)
    description = models.TextField()
    partnership_type = models.CharField(
        max_length=50, choices=partner_choices, default="collaborator"
    )
    created_at = models.DateTimeField(default=timezone.now)
    update_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def clean(self):
        if self.logo and self.logo.size > 2 * 1024 * 1024:  # Limite à 2MB
            raise ValidationError("Le logo ne peut pas dépasser 2MB.")

    class Meta:
        verbose_name = "Partenaire"


class Event(models.Model):
    type_choices = (("public", "Public"), ("private", "Privé"))
    uid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="event_user")
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    title = models.CharField(max_length=150)
    description = models.TextField()
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    location = models.CharField(max_length=150)
    image = models.ImageField(upload_to="event_images/", blank=True, null=True)
    type_event = models.CharField(max_length=10, choices=type_choices, default="public")
    partner = models.ManyToManyField(Partner, related_name="event_partner")
    statut = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Evenement"

    def get_disponibilite(self):
        """Retourne la disponibilité des tickets par type"""
        try:
            info_ticket = self.infoticket_event
            vendus = self.ticket_event.values("type_ticket").annotate(total=Count("id"))

            # Créer un dictionnaire des tickets vendus
            tickets_vendus = {item["type_ticket"]: item["total"] for item in vendus}

            return {
                "normal": {
                    "capacite": info_ticket.normal_capacity,
                    "vendus": tickets_vendus.get("normal", 0),
                    "disponibles": info_ticket.normal_capacity - tickets_vendus.get("normal", 0),
                },
                "vip": {
                    "capacite": info_ticket.vip_capacity,
                    "vendus": tickets_vendus.get("vip", 0),
                    "disponibles": info_ticket.vip_capacity - tickets_vendus.get("vip", 0),
                },
                "vvip": {
                    "capacite": info_ticket.vvip_capacity,
                    "vendus": tickets_vendus.get("vvip", 0),
                    "disponibles": info_ticket.vvip_capacity - tickets_vendus.get("vvip", 0),
                },
            }
        except InfoTicket.DoesNotExist:
            return None

    def verifier_disponibilite(self, type_ticket, quantite):
        """Vérifie si la quantité demandée est disponible pour un type de ticket"""
        disponibilite = self.get_disponibilite()
        if not disponibilite:
            return False

        return quantite <= disponibilite[type_ticket]["disponibles"]

    def total_tickets_disponibles(self):
        """Retourne le nombre total de tickets disponibles"""
        disponibilite = self.get_disponibilite()
        if not disponibilite:
            return 0

        return sum(type_info["disponibles"] for type_info in disponibilite.values())

    def clean(self):
        if self.start_date and self.end_date:
            if self.start_date > self.end_date:
                raise ValidationError("La date de début ne peut pas être après la date de fin.")
        if self.image and self.image.size > 2 * 1024 * 1024:
            raise ValidationError("L'image ne peut pas dépasser 2MB.")

        return super().clean()


class InfoTicket(models.Model):
    type_access = (("gratuit", "Gratuit"), ("payant", "Payant"))
    uid = models.UUIDField(default=uuid.uuid4, unique=True, editable=True)
    type_access = models.CharField(max_length=10, choices=type_access, default="payant")
    normal_capacity = models.IntegerField(default=0)
    vip_capacity = models.IntegerField(default=0)
    vvip_capacity = models.IntegerField(default=0)
    prix_normal = models.BigIntegerField(default=0)
    prix_vip = models.BigIntegerField(default=0)
    prix_vvip = models.BigIntegerField(default=0)
    event = models.OneToOneField(Event, on_delete=models.CASCADE, related_name="infoticket_event")
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Information du ticket pour {self.event}"

    def total_capacity(self):
        return self.normal_capacity + self.vip_capacity + self.vvip_capacity

    def clean(self):
        if self.normal_capacity < 0 or self.vip_capacity < 0 or self.vvip_capacity < 0:
            raise ValidationError("La capacité ne peut pas être négative.")

        if self.prix_normal < 0 or self.prix_vip < 0 or self.prix_vvip < 0:
            raise ValidationError("Les prix ne peuvent pas être négatifs.")

        if self.type_access == "gratuit" and (
            self.prix_normal > 0 or self.prix_vip > 0 or self.prix_vvip > 0
        ):
            raise ValidationError("Vous ne pouvez pas definir un prix pour un événement gratuit.")

        if self.prix_vip > 0 and self.vip_capacity == 0:
            raise ValidationError(
                "La capacité VIP doit être supérieure à 0 si le prix VIP est supérieur à 0."
            )
        if self.prix_vvip > 0 and self.vvip_capacity == 0 and self.type_access == "payant":
            raise ValidationError(
                "La capacité VVIP doit être supérieure à 0 si le prix VVIP est"
                + "supérieur à 0 pour un événement payant"
            )
        if self.vip_capacity > 0 and self.prix_vip == 0 and self.type_access == "payant":
            raise ValidationError(
                "Vous devez definir un prix VIP si la capacité VIP est supérieur"
                + "à 0 pour un événement payant"
            )
        if self.vvip_capacity > 0 and self.prix_vvip == 0 and self.type_access == "payant":
            raise ValidationError(
                "Vous devez definir un prix VVIP si la capacité VVIP est"
                + " supérieur à 0 pour un événement payant"
            )
        if self.normal_capacity <= 0:
            raise ValidationError("La capacité normale doit être supérieure à 0.")

        if self.type_access == "payant" and self.prix_normal == 0:
            raise ValidationError("Vous devez definir un prix pour un événement payant.")
        return super().clean()


class Payement(models.Model):
    mode_choices = [
        ("orange_money", "Orange money"),
        ("mobile_money", "Mobile money"),
        ("paycard", "Paycard"),
        ("visa", "VISA"),
    ]
    reference_payement = models.CharField(max_length=100, unique=True)
    nom_complet = models.CharField(max_length=150)
    email_reception = models.EmailField(null=True, blank=True)
    telephone_payement = models.CharField(max_length=20)
    telephone_reception = models.CharField(max_length=20, null=True, blank=True)
    payment_method = models.CharField(
        max_length=25, choices=mode_choices, default="orange_money", null=True, blank=True
    )
    statut_payement = models.BooleanField(default=False)
    quantity = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(default=timezone.now)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="payement_event")
    updated_at = models.DateTimeField(auto_now=True)
    amount = models.BigIntegerField(default=0)

    def save(self, *args, **kwargs):
        if not self.reference_payement:
            self.reference_payement = f"PE-PA-{uuid.uuid4().hex[:6]}".upper()
        if self.amount <= 0:
            raise ValidationError("Le montant doit être positif.")

        super().save(*args, **kwargs)

    def __str__(self):
        return self.reference_payement

    class Meta:
        verbose_name = "Payement"


class Ticket(models.Model):
    type_choices = (("normal", "Normal"), ("vip", "VIP"), ("vvip", "VVIP"))
    code_ticket = models.CharField(max_length=100, unique=True)
    qr_code = models.ImageField(upload_to="qr_codes/", blank=True, null=True)
    ticket_pdf = models.FileField(upload_to="tickets/", null=True, blank=True)
    payement = models.ForeignKey(
        Payement, on_delete=models.DO_NOTHING, related_name="ticket_payement"
    )
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="ticket_event")
    # ticket = models.ForeignKey(InfoTicket, on_delete=models.CASCADE, related_name="ticket_info")
    type_ticket = models.CharField(max_length=20, choices=type_choices, default="normal")
    scan_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.event.title

    def save(self, *args, **kwargs):
        if self.event.available_capacity() <= 0:
            raise ValidationError("Plus de places disponibles pour cet événement.")
        if not self.code_ticket:
            self.code_ticket = f"PE-TI-{uuid.uuid4().hex[:6]}".upper()
        if not self.qr_code:
            qr = qrcode.make(self.code_ticket)
            buffer = BytesIO()
            qr.save(buffer, format="PNG")
            self.qr_code.save(f"qr_{self.code_ticket}.png", File(buffer), save=False)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Ticket"


class Contact(models.Model):
    pass
