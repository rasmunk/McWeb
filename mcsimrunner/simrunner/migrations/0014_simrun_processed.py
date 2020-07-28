# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('simrunner', '0013_simrun_visualise'),
    ]

    operations = [
        migrations.AddField(
            model_name='simrun',
            name='processed',
            field=models.DateTimeField(null=True, verbose_name=b'date processed', blank=True)
        ),
    ]
