# Generated by Django 4.2.2 on 2023-07-06 13:21

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("user", "0006_alter_post_hashtag"),
    ]

    operations = [
        migrations.AlterField(
            model_name="user",
            name="username",
            field=models.CharField(max_length=60, unique=True),
        ),
    ]
