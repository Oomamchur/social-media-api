# Generated by Django 4.2.2 on 2023-07-05 16:41

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("user", "0004_like"),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name="like",
            unique_together={("post", "user")},
        ),
    ]
