# Generated by Django 5.1.1 on 2024-12-27 15:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('event', '0002_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='payement',
            name='amount',
            field=models.BigIntegerField(default=0),
        ),
    ]
