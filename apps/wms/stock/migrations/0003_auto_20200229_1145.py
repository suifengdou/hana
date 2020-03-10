# -*- coding: utf-8 -*-
# Generated by Django 1.11.25 on 2020-02-29 03:45
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0002_mydeptstock_transdeptstock'),
    ]

    operations = [
        migrations.AlterField(
            model_name='deptstockinfo',
            name='vwarehouse',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='vware', to='warehouse.WarehouseVirtual', verbose_name='部门仓'),
        ),
    ]