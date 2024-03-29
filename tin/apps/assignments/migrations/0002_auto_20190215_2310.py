# Generated by Django 2.1.5 on 2019-02-16 04:10

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('assignments', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='assignment',
            name='enable_grader_timeout',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='assignment',
            name='grader_timeout',
            field=models.IntegerField(default=5, validators=[django.core.validators.MinValueValidator(1)]),
        ),
    ]
