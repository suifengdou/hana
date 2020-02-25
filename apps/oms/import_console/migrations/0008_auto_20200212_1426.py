# -*- coding: utf-8 -*-
# Generated by Django 1.11.25 on 2020-02-12 14:26
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('import_console', '0007_auto_20200212_1329'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='oristockout',
            name='error_tag',
        ),
        migrations.AddField(
            model_name='oristockout',
            name='mistake_tag',
            field=models.SmallIntegerField(choices=[(0, '正常'), (1, '重复递交'), (2, '仓库非法'), (3, '部门非法'), (4, '货品非法')], default=0, verbose_name='错误原因'),
        ),
    ]