# Generated by Django 2.2.3 on 2019-07-25 16:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('submissions', '0008_submission_complete'),
    ]

    operations = [
        migrations.AlterField(
            model_name='submission',
            name='grader_errors',
            field=models.CharField(blank=True, max_length=2048),
        ),
        migrations.AlterField(
            model_name='submission',
            name='grader_output',
            field=models.CharField(blank=True, max_length=10240),
        ),
    ]
