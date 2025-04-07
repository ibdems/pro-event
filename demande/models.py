from uuid import uuid4

from django.db import models
from django.utils import timezone

from event.models import Event, InfoTicket
from users.models import User


# Create your models here.
class Service(models.Model):
    name = models.CharField(max_length=150)
    description = models.TextField()
    accronyme = models.CharField(max_length=20)

    def __str__(self):
        return self.name


class AnonymousUser(models.Model):
    first_name = models.CharField(max_length=60)
    last_name = models.CharField(max_length=40)
    email = models.EmailField()
    contact = models.CharField(max_length=20)

    def __str__(self):
        return self.email


class ServiceHotesse(models.Model):
    number_hotesse = models.IntegerField()
    start_date_service = models.DateTimeField()
    end_date_service = models.DateTimeField()
    besoin = models.TextField()

    def __str__(self):
        return self.number_hotesse


class Demande(models.Model):
    STATUS_CHOICES = (
        ("pending", "En attente"),
        ("accepted", "Acceptée"),
        ("rejected", "Rejetée"),
    )
    uid = models.UUIDField(default=uuid4, unique=True, editable=False)
    service = models.ManyToManyField(Service)
    event = models.OneToOneField(
        Event, on_delete=models.CASCADE, blank=True, null=True, related_name="event_demande"
    )
    ticket = models.OneToOneField(
        InfoTicket, on_delete=models.CASCADE, blank=True, null=True, related_name="ticket_demande"
    )
    anonymous_user = models.ForeignKey(
        AnonymousUser,
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name="anonymous_user_demande",
    )
    service_hotesse = models.OneToOneField(
        ServiceHotesse,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="service_hotesse_demande",
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, blank=True, null=True, related_name="user_demande"
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default="pending",
        verbose_name="Statut de la demande",
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
