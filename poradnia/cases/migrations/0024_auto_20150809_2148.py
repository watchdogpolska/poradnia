from django.db import migrations, models
from django.db.models import Count


def delete_empty(apps, schema_editor):
    # We get the model from the versioned app registry;
    # if we directly import it, it'll be the wrong version
    Case = apps.get_model("cases", "Case")
    pks = [
        x[0]
        for x in Case.objects.annotate(record_count=Count("record"))
        .filter(record_count=0)
        .values_list("id")
    ]
    Case.objects.filter(pk__in=pks).update(status="2")


class Migration(migrations.Migration):

    dependencies = [
        ("cases", "0023_auto_20150809_2131"),
        ("records", "0006_auto_20150503_1741"),
    ]

    operations = [migrations.RunPython(delete_empty)]
