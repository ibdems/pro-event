# Generated by Django 5.1.4 on 2025-02-16 12:47

import uuid

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("event", "0016_remove_ticket_ticket_img_ticket_ticket_pdf"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="event",
            name="normal_capacity",
        ),
        migrations.RemoveField(
            model_name="event",
            name="prix_normal",
        ),
        migrations.RemoveField(
            model_name="event",
            name="prix_vip",
        ),
        migrations.RemoveField(
            model_name="event",
            name="prix_vvip",
        ),
        migrations.RemoveField(
            model_name="event",
            name="type_access",
        ),
        migrations.RemoveField(
            model_name="event",
            name="vip_capacity",
        ),
        migrations.RemoveField(
            model_name="event",
            name="vvip_capacity",
        ),
        migrations.CreateModel(
            name="InfoTicket",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("uid", models.UUIDField(default=uuid.uuid4, unique=True)),
                (
                    "type_access",
                    models.CharField(
                        choices=[("gratuit", "Gratuit"), ("payant", "Payant")],
                        default="payant",
                        max_length=10,
                    ),
                ),
                ("normal_capacity", models.IntegerField(default=0)),
                ("vip_capacity", models.IntegerField(default=0)),
                ("vvip_capacity", models.IntegerField(default=0)),
                ("prix_normal", models.BigIntegerField(default=0)),
                ("prix_vip", models.BigIntegerField(default=0)),
                ("prix_vvip", models.BigIntegerField(default=0)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("update_at", models.DateTimeField(auto_now=True)),
                (
                    "event",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="infoticket_event",
                        to="event.event",
                    ),
                ),
            ],
        ),
    ]
