# Generated by Django 5.1.4 on 2025-01-13 18:12

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("event", "0006_alter_category_options_alter_event_options_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="event",
            name="category",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="event_category",
                to="event.category",
            ),
        ),
    ]
