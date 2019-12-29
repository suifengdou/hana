# -*- coding: utf-8 -*-
# Generated by Django 1.11.16 on 2019-12-29 19:07
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('department', '0001_initial'),
        ('warehouse', '0001_initial'),
        ('goods', '0002_auto_20191229_1658'),
        ('stock', '0004_auto_20191229_1658'),
    ]

    operations = [
        migrations.CreateModel(
            name='DistributionInfo',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('create_time', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('update_time', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('is_delete', models.BooleanField(default=False, verbose_name='删除标记')),
                ('creator', models.CharField(blank=True, max_length=90, null=True, verbose_name='创建者')),
                ('distribution_order_id', models.CharField(max_length=50, verbose_name='分配单号')),
                ('goods_id', models.CharField(db_index=True, max_length=60, verbose_name='物料编码')),
                ('quantity', models.IntegerField(verbose_name='分配数量')),
                ('memorandum', models.CharField(blank=True, max_length=200, null=True, verbose_name='备注')),
                ('order_status', models.SmallIntegerField(choices=[(0, '已取消'), (1, '未审核'), (2, '已审核')], default=1, verbose_name='单据状态')),
                ('error_tag', models.SmallIntegerField(choices=[(0, '正常'), (1, '可用库存不足'), (2, '正常'), (3, '正常')], default=0, verbose_name='错误原因')),
                ('department', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='department.DepartmentInfo', verbose_name='部门')),
                ('goods_name', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='goods.GoodsInfo', verbose_name='货品名称')),
                ('vwarehouse', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='vwaredis', to='warehouse.WarehouseVirtual', verbose_name='虚拟仓')),
                ('warehouse', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='stock.StockInfo', verbose_name='实仓')),
            ],
            options={
                'verbose_name': 'oms-预分配',
                'verbose_name_plural': 'oms-预分配',
                'db_table': 'oms_pdb_distribution',
            },
        ),
        migrations.CreateModel(
            name='Undistribution',
            fields=[
            ],
            options={
                'verbose_name': 'oms-未审核预分配',
                'verbose_name_plural': 'oms-未审核预分配',
                'proxy': True,
                'indexes': [],
            },
            bases=('predistribution.distributioninfo',),
        ),
    ]
