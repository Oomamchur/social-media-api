# Generated by Django 4.2.2 on 2023-06-30 13:43

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import user.models


class Migration(migrations.Migration):
    dependencies = [
        ("user", "0007_userfollowing_userfollowing_unique_followers"),
    ]

    operations = [
        migrations.CreateModel(
            name="Post",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("hashtag", models.CharField(max_length=60)),
                ("text", models.CharField(max_length=255)),
                (
                    "media_image",
                    models.ImageField(
                        null=True, upload_to=user.models.post_image_file_path
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="posts",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.DeleteModel(
            name="UserFollowing",
        ),
    ]
