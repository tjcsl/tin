# Generated by Django 2.2.12 on 2020-05-27 02:54

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('assignments', '0012_auto_20191006_1155'),
    ]

    operations = [
        migrations.AddField(
            model_name='assignment',
            name='submission_limit_cooldown',
            field=models.PositiveIntegerField(default=30, validators=[django.core.validators.MinValueValidator(10)]),
        ),
        migrations.AddField(
            model_name='assignment',
            name='submission_limit_count',
            field=models.PositiveIntegerField(default=90, validators=[django.core.validators.MinValueValidator(10)]),
        ),
        migrations.AddField(
            model_name='assignment',
            name='submission_limit_interval',
            field=models.PositiveIntegerField(default=30, validators=[django.core.validators.MinValueValidator(10)]),
        ),
    ]
