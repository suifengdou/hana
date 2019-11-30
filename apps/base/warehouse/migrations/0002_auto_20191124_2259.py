# -*- coding: utf-8 -*-
# Generated by Django 1.11.25 on 2019-11-24 22:59
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('warehouse', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='warehouseinfo',
            name='order_status',
            field=models.IntegerField(choices=[(0, '停用'), (1, '正常')], default=1, verbose_name='仓库状态'),
        ),
        migrations.AlterField(
            model_name='warehousetypeinfo',
            name='order_status',
            field=models.IntegerField(choices=[(0, '停用'), (1, '正常')], default=1, verbose_name='仓库状态'),
        ),
    ]