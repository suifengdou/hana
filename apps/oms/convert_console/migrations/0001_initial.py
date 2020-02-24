# -*- coding: utf-8 -*-
# Generated by Django 1.11.25 on 2020-02-23 16:01
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('goods', '0004_auto_20200222_0843'),
        ('company', '0002_auto_20200222_0910'),
        ('department', '0003_auto_20200223_0904'),
        ('warehouse', '0006_auto_20200223_1054'),
    ]

    operations = [
        migrations.CreateModel(
            name='CovertSI',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('create_time', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('update_time', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('is_delete', models.BooleanField(default=False, verbose_name='删除标记')),
                ('creator', models.CharField(blank=True, max_length=90, null=True, verbose_name='创建者')),
                ('order_id', models.CharField(db_index=True, max_length=60, unique=True, verbose_name='单据编号')),
                ('order_category', models.CharField(max_length=60, verbose_name='单据类型')),
                ('order_creator', models.SmallIntegerField(choices=[(0, '独立入库'), (1, '全局入库')], default=0, verbose_name='创建人')),
                ('create_date', models.DateTimeField(max_length=60, verbose_name='创建日期')),
                ('seller', models.CharField(max_length=60, verbose_name='结算方')),
                ('last_modifier', models.CharField(max_length=60, verbose_name='最后修改人')),
                ('payee', models.CharField(max_length=60, verbose_name='收款方')),
                ('stockin_date', models.DateTimeField(max_length=60, verbose_name='入库日期')),
                ('purchaser', models.CharField(max_length=60, verbose_name='采购组织')),
                ('goods_id', models.CharField(db_index=True, max_length=60, verbose_name='物料编码')),
                ('quantity_receivable', models.IntegerField(blank=True, null=True, verbose_name='应收数量')),
                ('quantity_received', models.IntegerField(verbose_name='实收数量')),
                ('batch_number', models.CharField(max_length=60, verbose_name='批号')),
                ('expiry_date', models.DateTimeField(max_length=60, verbose_name='有效期至')),
                ('produce_date', models.DateTimeField(max_length=60, verbose_name='生产日期')),
                ('memorandum', models.CharField(blank=True, max_length=60, null=True, verbose_name='备注')),
                ('origin_order_category', models.CharField(max_length=60, verbose_name='源单类型')),
                ('origin_order_id', models.CharField(max_length=60, verbose_name='源单编号')),
                ('price', models.IntegerField(verbose_name='单价')),
                ('quantity_linking', models.IntegerField(default=0, verbose_name='关联存货数量')),
                ('order_status', models.SmallIntegerField(choices=[(0, '已取消'), (1, '未审核'), (2, '已完成')], db_index=True, default=1, verbose_name='订单状态')),
                ('mistake_tag', models.SmallIntegerField(choices=[(0, '正常'), (1, '原始单缺漏'), (2, '入库数量大于采购数量'), (3, '保存库存错误'), (4, '货品错误'), (5, '采购单错误'), (5, '采购单数量错误')], default=0, verbose_name='错误标识')),
                ('department', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='department.DepartmentInfo', verbose_name='部门')),
                ('goods_name', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='goods.GoodsInfo', verbose_name='物料名称')),
                ('supplier', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='company.CompanyInfo', verbose_name='供货方')),
                ('warehouse', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='warehouse.WarehouseInfo', verbose_name='仓库')),
            ],
            options={
                'verbose_name': 'oms-入库调整单查询',
                'verbose_name_plural': 'oms-入库调整单查询',
                'db_table': 'oms_convert_stockin',
            },
        ),
        migrations.CreateModel(
            name='CovertSIUnhandle',
            fields=[
            ],
            options={
                'verbose_name': 'oms-入库调整单未审核',
                'verbose_name_plural': 'oms-入库调整单未审核',
                'proxy': True,
                'indexes': [],
            },
            bases=('convert_console.covertsi',),
        ),
    ]
