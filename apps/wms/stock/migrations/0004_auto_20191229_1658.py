# -*- coding: utf-8 -*-
# Generated by Django 1.11.16 on 2019-12-29 16:58
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0003_auto_20191228_2053'),
    ]

    operations = [
        migrations.AlterField(
            model_name='deptstockinfo',
            name='goods_id',
            field=models.CharField(db_index=True, max_length=60, verbose_name='物料编码'),
        ),
        migrations.AlterField(
            model_name='stockinfo',
            name='goods_id',
            field=models.CharField(db_index=True, max_length=60, verbose_name='物料编码'),
        ),
    ]