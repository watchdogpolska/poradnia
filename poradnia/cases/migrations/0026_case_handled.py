
from django.db import migrations, models


def migrate_handled(apps, schema_editor):
    # We can't import the Person model directly as it may be a newer
    # version than this migration expects. We use the historical version.
    Letter = apps.get_model("letters", "Letter")
    Case = apps.get_model('cases', "Case")
    for case in Case.objects.all():
        try:
            obj = Letter.objects.filter(case=case).filter(status='done').order_by('-created_on', '-id').all()[0]
            if obj.created_by.is_staff:
                case.handled = True
                case.save()
            else:
                case.handled = False
        except IndexError:
            case.handled = False


class Migration(migrations.Migration):

    dependencies = [
        ('cases', '0025_auto_20150810_1440'),
        ('letters', '0008_letter_eml'),
        ('users', '0005_auto_20150712_1524')

    ]

    operations = [
        migrations.AddField(
           model_name='case',
           name='handled',
           field=models.BooleanField(default=False, verbose_name='Handled'),
           preserve_default=True,
        ),
        migrations.RunPython(migrate_handled),
    ]
