# Generated by Django 3.2.14 on 2022-08-14 18:32

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='is_sysadmin',
        ),
    ]
