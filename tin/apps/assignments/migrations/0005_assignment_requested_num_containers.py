# Generated by Django 2.2.3 on 2019-07-30 19:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('assignments', '0004_assignment_has_network_access'),
    ]

    operations = [
        migrations.AddField(
            model_name='assignment',
            name='requested_num_containers',
            field=models.IntegerField(default=-1),
        ),
    ]