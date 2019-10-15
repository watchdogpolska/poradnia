
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('cases', '0004_auto_20150304_1650'),
    ]

    operations = [
        migrations.CreateModel(
            name='CaseGroupObjectPermission',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('content_object', models.ForeignKey(to='cases.Case')),
                ('group', models.ForeignKey(to='auth.Group')),
                ('permission', models.ForeignKey(to='auth.Permission')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='CaseUserObjectPermission',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('content_object', models.ForeignKey(to='cases.Case')),
                ('permission', models.ForeignKey(to='auth.Permission')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='caseuserobjectpermission',
            unique_together=set([('user', 'permission', 'content_object')]),
        ),
        migrations.AlterUniqueTogether(
            name='casegroupobjectpermission',
            unique_together=set([('group', 'permission', 'content_object')]),
        ),
        migrations.AlterModelOptions(
            name='case',
            options={'permissions': (('can_view_all', 'Can view all cases'), ('can_view', 'Can view'), ('can_select_client', 'Can select client'), ('can_assign', 'Can assign new permissions'))},
        ),
    ]
