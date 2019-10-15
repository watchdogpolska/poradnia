
from django.conf import settings
from django.db import migrations, models
from django.utils.timezone import now


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('advicer', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='advice',
            options={'ordering': ['created_on'], 'permissions': ('can_view_all_advices', 'Can view all advices')},
        ),
        migrations.RemoveField(
            model_name='advice',
            name='who',
        ),
        migrations.AddField(
            model_name='advice',
            name='advicer',
            field=models.ForeignKey(on_delete=models.CASCADE,default=1, verbose_name='Advicer', to=settings.AUTH_USER_MODEL, help_text='Person who give a advice'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='advice',
            name='area',
            field=models.ForeignKey(on_delete=models.CASCADE,verbose_name='Area', blank=True, to='advicer.Area', null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='advice',
            name='comment',
            field=models.TextField(verbose_name='Comment'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='advice',
            name='created_by',
            field=models.ForeignKey(on_delete=models.CASCADE,related_name='advice_created_by', verbose_name='Created by', to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='advice',
            name='created_on',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Created on'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='advice',
            name='grant_on',
            field=models.DateTimeField(default=now, verbose_name='Grant on'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='advice',
            name='institution_kind',
            field=models.ForeignKey(on_delete=models.CASCADE,verbose_name='Kind of institution', blank=True, to='advicer.InstitutionKind', null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='advice',
            name='issues',
            field=models.ManyToManyField(to='advicer.Issue', null=True, verbose_name='Issues', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='advice',
            name='modified_by',
            field=models.ForeignKey(on_delete=models.CASCADE,related_name='advice_modified_by', verbose_name='Modified by', to=settings.AUTH_USER_MODEL, null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='advice',
            name='modified_on',
            field=models.DateTimeField(auto_now=True, verbose_name='Modified on', null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='advice',
            name='person_kind',
            field=models.ForeignKey(on_delete=models.CASCADE,verbose_name='Kind of person ', blank=True, to='advicer.PersonKind', null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='advice',
            name='subject',
            field=models.CharField(max_length=50, null=True, verbose_name='Subject', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='advice',
            name='visible',
            field=models.BooleanField(default=True, verbose_name='Visible'),
            preserve_default=True,
        ),
    ]
