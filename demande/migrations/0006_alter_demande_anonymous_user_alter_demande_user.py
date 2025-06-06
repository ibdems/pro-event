# Generated by Django 5.1.7 on 2025-04-03 10:40

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("demande", "0005_rename_end_date_servicehotesse_end_date_service_and_more"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name="demande",
            name="anonymous_user",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="anonymous_user_demande",
                to="demande.anonymoususer",
            ),
        ),
        migrations.AlterField(
            model_name="demande",
            name="user",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="user_demande",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
