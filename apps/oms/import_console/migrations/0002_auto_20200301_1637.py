# -*- coding: utf-8 -*-
# Generated by Django 1.11.25 on 2020-03-01 16:37
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('import_console', '0001_initial'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='oristockininfo',
            unique_together=set([('detail_num', 'order_id')]),
        ),
    ]