# -*- coding: utf-8 -*-
# Generated by Django 1.11.16 on 2019-12-29 16:58
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('goods', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='goodsinfo',
            name='goods_id',
            field=models.CharField(db_index=True, max_length=150, unique=True, verbose_name='货品代码'),
        ),
    ]
