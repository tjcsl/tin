# Generated by Django 4.2.13 on 2024-05-27 21:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("assignments", "0030_quizlogmessage_assignment_is_quiz_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="assignment",
            name="quiz_autocomplete_enabled",
            field=models.BooleanField(default=False),
        ),
    ]
