# -*- coding: utf-8 -*-
# Generated by Django 1.11.25 on 2020-02-22 22:07
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('relationship', '0004_auto_20200222_2206'),
    ]

    operations = [
        migrations.AlterField(
            model_name='departmenttovwarehouse',
            name='department',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='department.DepartmentInfo', verbose_name='部门名称'),
        ),
    ]
