# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('simrunner', '0012_simrun_copyall'),
    ]

    operations = [
        migrations.AddField(
            model_name='simrun',
            name='skipvisualisation',
            field=models.BooleanField(default=False),
        ),
    ]
