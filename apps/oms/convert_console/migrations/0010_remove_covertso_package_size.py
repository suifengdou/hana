# -*- coding: utf-8 -*-
# Generated by Django 1.11.16 on 2020-02-25 15:36
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('convert_console', '0009_auto_20200225_1435'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='covertso',
            name='package_size',
        ),
    ]
