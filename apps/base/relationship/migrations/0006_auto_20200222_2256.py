# -*- coding: utf-8 -*-
# Generated by Django 1.11.25 on 2020-02-22 22:56
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('relationship', '0005_auto_20200222_2207'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='DepartmentToVWarehouse',
            new_name='DeptToVW',
        ),
        migrations.RenameModel(
            old_name='DepartmentToWarehouse',
            new_name='DeptToW',
        ),
    ]