# -*- coding: utf-8 -*-
# Generated by Django 1.11.16 on 2019-12-28 16:30
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
                ('category', models.SmallIntegerField(choices=[(0, '普通仓库'), (1, '工厂仓库'), (2, '虚拟仓库')], default=0, verbose_name='仓库类型')),
                ('order_status', models.SmallIntegerField(choices=[(0, '停用'), (1, '正常')], default=1, verbose_name='仓库状态')),
            ],
            options={
                'verbose_name': 'BASE-仓库',
                'verbose_name_plural': 'BASE-仓库',
                'db_table': 'base_wah_warehouse',
            },
        ),
        migrations.CreateModel(
            name='WarehouseGeneral',
            fields=[
            ],
            options={
                'verbose_name': 'BASE-仓库-普通仓库',
                'verbose_name_plural': 'BASE-仓库-普通仓库',
                'proxy': True,
                'indexes': [],
            },
            bases=('warehouse.warehouseinfo',),
        ),
        migrations.CreateModel(
            name='WarehouseManu',
            fields=[
            ],
            options={
                'verbose_name': 'BASE-仓库-工厂仓库',
                'verbose_name_plural': 'BASE-仓库-工厂仓库',
                'proxy': True,
                'indexes': [],
            },
            bases=('warehouse.warehouseinfo',),
        ),
        migrations.CreateModel(
            name='WarehouseVirtual',
            fields=[
            ],
            options={
                'verbose_name': 'BASE-仓库-虚拟仓库',
                'verbose_name_plural': 'BASE-仓库-虚拟仓库',
                'proxy': True,
                'indexes': [],
            },
            bases=('warehouse.warehouseinfo',),
        ),
    ]
