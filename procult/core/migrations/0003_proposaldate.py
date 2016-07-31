# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


def create_configs(apps, schema_editor):
    ProposalDate = apps.get_model('core', 'ProposalDate')

    p = ProposalDate()
    p.save()


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_auto_20160308_1329'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProposalDate',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('is_available', models.BooleanField(default=False)),
            ],
        ),
        migrations.RunPython(create_configs),
    ]
