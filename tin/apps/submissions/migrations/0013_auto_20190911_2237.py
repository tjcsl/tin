# Generated by Django 2.2.5 on 2019-09-12 02:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('submissions', '0012_submission_grader_pid'),
    ]

    operations = [
        migrations.AlterField(
            model_name='submission',
            name='grader_pid',
            field=models.IntegerField(blank=True, default=None, null=True),
        ),
    ]