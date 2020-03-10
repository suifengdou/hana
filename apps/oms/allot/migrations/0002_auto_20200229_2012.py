# -*- coding: utf-8 -*-
# Generated by Django 1.11.25 on 2020-02-29 12:12
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('allot', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='vallotsiinfo',
            name='vwarehouse',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='asi_vware', to='warehouse.WarehouseVirtual', verbose_name='目的部门仓'),
        ),
    ]