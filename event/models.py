import uuid
from io import BytesIO

import qrcode
from django.core.files import File
from django.db import models
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
    type_access = (("gratuit", "Gratuit"), ("payant", "Payant"))
    uid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="event_user")
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    title = models.CharField(max_length=150)
    description = models.TextField()
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    location = models.CharField(max_length=150)
    normal_capacity = models.IntegerField(default=0)
    vip_capacity = models.IntegerField(default=0)
    vvip_capacity = models.IntegerField(default=0)
    prix_normal = models.BigIntegerField(default=0)
    prix_vip = models.BigIntegerField(default=0)
    prix_vvip = models.BigIntegerField(default=0)
    image = models.ImageField(upload_to="event_images/", blank=True, null=True)
    type_event = models.CharField(max_length=10, choices=type_choices, default="public")
    partner = models.ManyToManyField(Partner, related_name="event_partner", null=True, blank=True)
    statut = models.BooleanField(default=True)
    type_access = models.CharField(max_length=10, choices=type_access, default="payant")
    created_at = models.DateTimeField(default=timezone.now)
    update_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Evenement"

    def total_capacity(self):
        return self.normal_capacity + self.vip_capacity + self.vvip_capacity

    def available_capacity(self):
        tickets_sold = self.ticket_event.count()
        return self.total_capacity() - tickets_sold

    def save(self, *args, **kwargs):
        print(f"Start Date: {self.start_date}, End Date: {self.end_date}")
        super().save(*args, **kwargs)

    def clean(self):
        if self.normal_capacity < 0 or self.vip_capacity < 0 or self.vvip_capacity < 0:
            raise ValidationError("La capacité ne peut pas être négative.")
        print(f"Start Date: {self.start_date}, End Date: {self.end_date}")
        if self.start_date and self.end_date:
            if self.start_date > self.end_date:
                raise ValidationError("La date de début ne peut pas être après la date de fin.")
        if self.image and self.image.size > 2 * 1024 * 1024:
            raise ValidationError("L'image ne peut pas dépasser 2MB.")
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
        if self.vvip_capacity > 0 and self.vvip_capacity == 0 and self.type_access == "payant":
            raise ValidationError(
                "Vous devez definir un prix VVIP si la capacité VVIP est"
                + " supérieur à 0 pour un événement payant"
            )
        if self.normal_capacity <= 0:
            raise ValidationError("La capacité normale doit être supérieure à 0.")

        if self.type_access == "payant" and self.prix_normal == 0:
            raise ValidationError("Vous devez definir un prix pour un événement payant.")

        return super().clean()


class Ticket(models.Model):
    code_ticket = models.CharField(max_length=100, unique=True)
    email_reception = models.EmailField(null=True, blank=True)
    telephone_payement = models.CharField(max_length=20)
    telephone_reception = models.CharField(max_length=20, null=True, blank=True)
    statut_payement = models.BooleanField(default=False)
    qr_code = models.ImageField(upload_to="qr_codes/", blank=True, null=True)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="ticket_event")
    scan_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)
    update_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.event.title

    def save(self, *args, **kwargs):
        if not self.code_ticket:
            self.code_ticket = f"PE-TI-{uuid.uuid4().hex[:6]}"
        if not self.qr_code:
            qr = qrcode.make(f"{self.event.title}-{self.code_ticket}")
            buffer = BytesIO()
            qr.save(buffer, format="PNG")
            self.qr_code.save(f"qr_{self.code_ticket}.png", File(buffer), save=False)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Ticket"


class Payement(models.Model):
    reference_payement = models.CharField(max_length=100, unique=True)
    tickets = models.ManyToManyField(Ticket, related_name="payements")
    created_at = models.DateTimeField(default=timezone.now)
    update_at = models.DateTimeField(auto_now=True)
    amount = models.BigIntegerField(default=0)

    def save(self, *args, **kwargs):
        if not self.reference_payement:
            self.reference_payement = f"PE-PA-{uuid.uuid4().hex[:6]}"
        if self.amount <= 0:
            raise ValidationError("Le montant doit être positif.")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Paiement pour {self.tickets.count()} billets"

    class Meta:
        verbose_name = "Payement"


class Contact(models.Model):
    pass
