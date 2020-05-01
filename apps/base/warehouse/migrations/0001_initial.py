# -*- coding: utf-8 -*-
# Generated by Django 1.11.25 on 2020-04-25 16:30
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='WarehouseInfo',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('create_time', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('update_time', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('is_delete', models.BooleanField(default=False, verbose_name='删除标记')),
                ('creator', models.CharField(blank=True, max_length=90, null=True, verbose_name='创建者')),
                ('warehouse_name', models.CharField(max_length=60, unique=True, verbose_name='仓库名称')),
                ('warehouse_id', models.CharField(max_length=20, unique=True, verbose_name='仓库ID')),
                ('nation', models.CharField(blank=True, max_length=50, null=True, verbose_name='国别')),
                ('province', models.CharField(blank=True, max_length=50, null=True, verbose_name='省份')),
                ('city', models.CharField(blank=True, max_length=50, null=True, verbose_name='城市')),
                ('district', models.CharField(blank=True, max_length=50, null=True, verbose_name='区县')),
                ('consignee', models.CharField(blank=True, max_length=50, null=True, verbose_name='收货人')),
                ('mobile', models.CharField(blank=True, max_length=30, null=True, verbose_name='电话')),
                ('address', models.CharField(blank=True, max_length=90, null=True, verbose_name='地址')),
                ('memorandum', models.CharField(blank=True, max_length=90, null=True, verbose_name='地址')),
                ('attribute', models.SmallIntegerField(choices=[(0, '自有本仓'), (1, '自有外仓'), (2, '寄售仓'), (3, '直营仓')], default=0, verbose_name='仓库属性')),
                ('category', models.SmallIntegerField(choices=[(0, '普通仓库'), (1, '第三方仓储')], default=0, verbose_name='仓库类型')),
                ('order_status', models.SmallIntegerField(choices=[(0, '停用'), (1, '正常')], default=1, verbose_name='仓库状态')),
            ],
            options={
                'verbose_name': 'BASE-仓库-实物仓库',
                'verbose_name_plural': 'BASE-仓库-实物仓库',
                'db_table': 'base_wah_warehouse',
            },
        ),
        migrations.CreateModel(
            name='WarehouseVirtual',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('create_time', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('update_time', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('is_delete', models.BooleanField(default=False, verbose_name='删除标记')),
                ('creator', models.CharField(blank=True, max_length=90, null=True, verbose_name='创建者')),
                ('warehouse_name', models.CharField(max_length=60, unique=True, verbose_name='仓库名称')),
                ('warehouse_id', models.CharField(max_length=20, unique=True, verbose_name='仓库ID')),
                ('nation', models.CharField(blank=True, max_length=50, null=True, verbose_name='国别')),
                ('province', models.CharField(blank=True, max_length=50, null=True, verbose_name='省份')),
                ('city', models.CharField(blank=True, max_length=50, null=True, verbose_name='城市')),
                ('district', models.CharField(blank=True, max_length=50, null=True, verbose_name='区县')),
                ('consignee', models.CharField(blank=True, max_length=50, null=True, verbose_name='收货人')),
                ('mobile', models.CharField(blank=True, max_length=30, null=True, verbose_name='电话')),
                ('address', models.CharField(blank=True, max_length=90, null=True, verbose_name='地址')),
                ('memorandum', models.CharField(blank=True, max_length=90, null=True, verbose_name='地址')),
                ('category', models.SmallIntegerField(choices=[(0, '部门仓库'), (1, '全局正品'), (2, '全局残品')], default=0, verbose_name='仓库类型')),
                ('order_status', models.SmallIntegerField(choices=[(0, '停用'), (1, '正常')], default=1, verbose_name='仓库状态')),
            ],
            options={
                'verbose_name': 'BASE-仓库-虚拟仓库',
                'verbose_name_plural': 'BASE-仓库-虚拟仓库',
                'db_table': 'base_wah_virtual',
            },
        ),
    ]
