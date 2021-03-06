# -*- coding: utf-8 -*-
# Generated by Django 1.11.25 on 2020-05-31 09:18
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('allot', '0003_auto_20200510_1029'),
    ]

    operations = [
        migrations.AlterField(
            model_name='vallotsoinfo',
            name='mistake_tag',
            field=models.SmallIntegerField(choices=[(0, '正常'), (1, '调拨数量不足'), (2, '更新虚拟库存错误'), (3, '单据保存出错'), (4, '保存部门仓失败'), (5, '保存实仓失败'), (6, '保存部门仓失败'), (7, '部门没有此货品'), (8, '批量分拨订单')], default=0, verbose_name='异常信息'),
        ),
    ]
