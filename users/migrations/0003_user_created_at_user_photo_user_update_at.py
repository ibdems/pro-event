# Generated by Django 5.1.1 on 2024-12-27 20:12

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_alter_user_contact'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='created_at',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AddField(
            model_name='user',
            name='photo',
            field=models.ImageField(blank=True, null=True, upload_to='', verbose_name='photo_user/'),
        ),
        migrations.AddField(
            model_name='user',
            name='update_at',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
