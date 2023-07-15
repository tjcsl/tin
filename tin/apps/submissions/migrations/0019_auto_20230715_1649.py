# Generated by Django 3.2.19 on 2023-07-15 20:49

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('submissions', '0018_comment'),
    ]

    operations = [
        migrations.AddField(
            model_name='comment',
            name='end_char',
            field=models.IntegerField(default=1, validators=[django.core.validators.MinValueValidator(1)]),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='comment',
            name='start_char',
            field=models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)]),
            preserve_default=False,
        ),
    ]