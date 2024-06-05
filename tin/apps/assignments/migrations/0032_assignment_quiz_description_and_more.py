# Generated by Django 4.2.13 on 2024-06-05 02:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("assignments", "0031_assignment_quiz_autocomplete_enabled"),
    ]

    operations = [
        migrations.AddField(
            model_name="assignment",
            name="quiz_description",
            field=models.CharField(blank=True, default="", max_length=4096),
        ),
        migrations.AddField(
            model_name="assignment",
            name="quiz_description_markdown",
            field=models.BooleanField(default=False),
        ),
    ]
