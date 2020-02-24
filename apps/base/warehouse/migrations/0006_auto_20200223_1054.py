# -*- coding: utf-8 -*-
# Generated by Django 1.11.25 on 2020-02-23 10:54
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('warehouse', '0005_auto_20200222_1918'),
    ]

    operations = [
        migrations.AlterField(
            model_name='warehousevirtual',
            name='category',
            field=models.SmallIntegerField(choices=[(0, '部门仓库'), (1, '全局正品'), (2, '全局残品')], default=0, verbose_name='仓库类型'),
        ),
    ]
