# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('simrunner', '0010_auto_20190903_1410'),
    ]

    operations = [
        migrations.AddField(
            model_name='simrun',
            name='runremote',
            field=models.BooleanField(default=False),
        ),
    ]
