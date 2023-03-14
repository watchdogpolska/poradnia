import django.utils.timezone
import model_utils.fields
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]

    operations = [
        migrations.CreateModel(
            name="Attachment",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        serialize=False,
                        auto_created=True,
                        primary_key=True,
                    ),
                ),
                ("attachment", models.FileField(upload_to=b"letters/%Y/%m/%d")),
                ("text", models.CharField(max_length=150)),
            ],
            options={},
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="Letter",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        serialize=False,
                        auto_created=True,
                        primary_key=True,
                    ),
                ),
                (
                    "status",
                    model_utils.fields.StatusField(
                        default=b"staff",
                        max_length=100,
                        no_check_for_status=True,
                        choices=[(b"staff", b"staff"), (b"done", b"done")],
                    ),
                ),
                (
                    "genre",
                    models.CharField(
                        default=b"mail",
                        max_length=20,
                        choices=[(b"mail", b"mail"), (b"comment", b"comment")],
                    ),
                ),
                (
                    "status_changed",
                    model_utils.fields.MonitorField(
                        default=django.utils.timezone.now, monitor=b"status"
                    ),
                ),
                (
                    "accept",
                    model_utils.fields.MonitorField(
                        default=django.utils.timezone.now,
                        when={b"done"},
                        monitor=b"status",
                    ),
                ),
                ("name", models.CharField(max_length=250)),
                ("text", models.TextField()),
                ("created_on", models.DateTimeField(auto_now_add=True)),
                ("modified_on", models.DateTimeField(auto_now=True, null=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        related_name="letter_created",
                        on_delete=models.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "modified_by",
                    models.ForeignKey(
                        related_name="letter_modified",
                        on_delete=models.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                        null=True,
                    ),
                ),
                (
                    "send_by",
                    models.ForeignKey(
                        related_name="senders",
                        on_delete=models.CASCADE,
                        blank=True,
                        to=settings.AUTH_USER_MODEL,
                        null=True,
                    ),
                ),
            ],
            options={"abstract": False},
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name="attachment",
            name="letter",
            field=models.ForeignKey(on_delete=models.CASCADE, to="letters.Letter"),
            preserve_default=True,
        ),
    ]
