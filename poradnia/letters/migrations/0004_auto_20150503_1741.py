import django.utils.timezone
import model_utils.fields
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("django_mailbox", "0003_auto_20150409_0316"),
        ("letters", "0003_remove_attachment_text"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="attachment",
            options={
                "verbose_name": "Attachment",
                "verbose_name_plural": "Attachments",
            },
        ),
        migrations.AlterModelOptions(
            name="letter",
            options={"verbose_name": "Letter", "verbose_name_plural": "Letters"},
        ),
        migrations.RemoveField(model_name="letter", name="send_by"),
        migrations.AddField(
            model_name="letter",
            name="message",
            field=models.ForeignKey(
                on_delete=models.CASCADE,
                blank=True,
                to="django_mailbox.Message",
                null=True,
            ),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name="letter",
            name="signature",
            field=models.TextField(null=True, verbose_name="Signature", blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name="letter",
            name="accept",
            field=model_utils.fields.MonitorField(
                default=django.utils.timezone.now,
                when={b"done"},
                verbose_name="Accepted on",
                monitor=b"status",
            ),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name="letter",
            name="created_by",
            field=models.ForeignKey(
                on_delete=models.CASCADE,
                related_name="letter_created_by",
                verbose_name="Created by",
                to=settings.AUTH_USER_MODEL,
            ),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name="letter",
            name="created_on",
            field=models.DateTimeField(auto_now_add=True, verbose_name="Created on"),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name="letter",
            name="genre",
            field=models.CharField(
                default=b"comment",
                max_length=20,
                choices=[(b"mail", b"mail"), (b"comment", b"comment")],
            ),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name="letter",
            name="modified_by",
            field=models.ForeignKey(
                on_delete=models.CASCADE,
                related_name="letter_modified_by",
                verbose_name="Modified by",
                to=settings.AUTH_USER_MODEL,
                null=True,
            ),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name="letter",
            name="modified_on",
            field=models.DateTimeField(
                auto_now=True, verbose_name="Modified on", null=True
            ),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name="letter",
            name="name",
            field=models.CharField(max_length=250, verbose_name="Subject"),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name="letter",
            name="text",
            field=models.TextField(verbose_name="Comment"),
            preserve_default=True,
        ),
    ]
