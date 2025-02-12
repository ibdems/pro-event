from uuid import uuid4

from django.db import models

from event.models import Event
from users.models import User


# Create your models here.
class Service(models.Model):
    name = models.CharField(max_length=150)
    description = models.TextField()

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
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    besoin = models.TextField()  # Besoin particuliers (tenue, langue parles, ethnique.....)

    def __str__(self):
        return self.number_hotesse


class Demande(models.Model):
    uid = models.UUIDField(default=uuid4, unique=True, editable=False)
    service = models.ManyToManyField(Service)
    event = models.OneToOneField(
        Event, on_delete=models.CASCADE, blank=True, null=True, related_name="event_demande"
    )
    anonymous_user = models.OneToOneField(
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
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, blank=True, null=True, related_name="user_demande"
    )
