# Generated by Django 5.1.4 on 2025-02-16 15:09

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("event", "0017_remove_event_normal_capacity_and_more"),
    ]

    operations = [
        migrations.RenameField(
            model_name="event",
            old_name="update_at",
            new_name="updated_at",
        ),
        migrations.RenameField(
            model_name="infoticket",
            old_name="update_at",
            new_name="updated_at",
        ),
        migrations.RenameField(
            model_name="payement",
            old_name="update_at",
            new_name="updated_at",
        ),
        migrations.RenameField(
            model_name="ticket",
            old_name="update_at",
            new_name="updated_at",
        ),
    ]
