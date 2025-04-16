# Generated by Django 5.1.7 on 2025-04-16 08:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("event", "0023_alter_contact_email_alter_contact_is_read_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="partner",
            name="is_platform_partner",
            field=models.BooleanField(
                default=False,
                help_text="Indique si le partenaire est un partenaire de la plateforme (ProEvent) et non d'un événement particulier",
            ),
        ),
    ]
