# -*- coding: utf-8 -*-
# Generated by Django 1.11.25 on 2020-02-18 21:17
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('import_console', '0012_auto_20200218_2109'),
    ]

    operations = [
        migrations.AlterField(
            model_name='orinsstockout',
            name='order_id',
            field=models.CharField(db_index=True, max_length=60, verbose_name='单据编号'),
        ),
    ]
