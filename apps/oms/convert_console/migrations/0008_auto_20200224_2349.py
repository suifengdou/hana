# -*- coding: utf-8 -*-
# Generated by Django 1.11.25 on 2020-02-24 23:49
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('convert_console', '0007_auto_20200224_2157'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='covertsi',
            name='last_modifier',
        ),
        migrations.AddField(
            model_name='covertsi',
            name='ori_creator',
            field=models.CharField(blank=True, max_length=60, null=True, verbose_name='创建人'),
        ),
    ]
