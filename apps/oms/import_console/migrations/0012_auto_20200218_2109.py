# -*- coding: utf-8 -*-
# Generated by Django 1.11.25 on 2020-02-18 21:09
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('import_console', '0011_auto_20200218_2105'),
    ]

    operations = [
        migrations.AlterField(
            model_name='orinsstockout',
            name='customer',
            field=models.CharField(blank=True, max_length=50, null=True, verbose_name='客户'),
        ),
    ]