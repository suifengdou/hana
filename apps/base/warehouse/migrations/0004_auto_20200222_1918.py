# -*- coding: utf-8 -*-
# Generated by Django 1.11.25 on 2020-02-22 19:18
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('warehouse', '0003_auto_20200222_1916'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='warehouseinfo',
            options={'verbose_name': 'BASE-实物仓库', 'verbose_name_plural': 'BASE-实物仓库'},
        ),
    ]
