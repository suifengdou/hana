# -*- coding: utf-8 -*-
# Generated by Django 1.11.25 on 2020-02-24 21:57
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('convert_console', '0006_auto_20200223_2328'),
    ]

    operations = [
        migrations.AlterField(
            model_name='covertso',
            name='memorandum',
            field=models.CharField(blank=True, max_length=300, null=True, verbose_name='备注'),
        ),
        migrations.AlterField(
            model_name='covertso',
            name='order_category',
            field=models.SmallIntegerField(choices=[(0, '独立出库'), (1, '全局出库')], default=0, verbose_name='单据类型'),
        ),
    ]