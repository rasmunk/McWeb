# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('simrunner', '0011_simrun_runremote'),
    ]

    operations = [
        migrations.AddField(
            model_name='simrun',
            name='copyall',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='simrun',
            name='extrafiles',
            field=models.CharField(default=b'[]', max_length=2000)
        )
    ]
