# Generated by Django 4.2.3 on 2023-07-11 19:00

from django.db import migrations, models
import user.models


class Migration(migrations.Migration):
    dependencies = [
        ("user", "0007_alter_user_username"),
    ]

    operations = [
        migrations.AlterField(
            model_name="user",
            name="image",
            field=models.ImageField(
                blank=True, null=True, upload_to=user.models.user_image_file_path
            ),
        ),
    ]
