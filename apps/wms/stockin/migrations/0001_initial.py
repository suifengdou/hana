# -*- coding: utf-8 -*-
# Generated by Django 1.11.16 on 2019-12-23 22:00
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('company', '0001_initial'),
        ('goods', '0001_initial'),
        ('warehouse', '0001_initial'),
        ('purchase', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='OriStockInInfo',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('create_time', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('update_time', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('is_delete', models.BooleanField(default=False, verbose_name='删除标记')),
                ('creator', models.CharField(blank=True, max_length=90, null=True, verbose_name='创建者')),
                ('order_category', models.CharField(max_length=60, verbose_name='单据类型')),
                ('to_organization', models.CharField(blank=True, max_length=60, null=True, verbose_name='对应组织')),
                ('order_creator', models.CharField(max_length=60, verbose_name='创建人')),
                ('supplier', models.CharField(max_length=60, verbose_name='供货方')),
                ('supplier_address', models.CharField(blank=True, max_length=60, null=True, verbose_name='供货方地址')),
                ('create_date', models.DateTimeField(max_length=60, verbose_name='创建日期')),
                ('seller', models.CharField(max_length=60, verbose_name='结算方')),
                ('bs_category', models.CharField(max_length=60, verbose_name='业务类型')),
                ('stockin_order_id', models.CharField(max_length=60, verbose_name='单据编号')),
                ('last_modifier', models.CharField(max_length=60, verbose_name='最后修改人')),
                ('payee', models.CharField(max_length=60, verbose_name='收款方')),
                ('stockin_time', models.DateTimeField(max_length=60, verbose_name='入库日期')),
                ('last_modify_time', models.DateTimeField(max_length=60, verbose_name='最后修改日期')),
                ('consignee', models.CharField(max_length=60, verbose_name='收料组织')),
                ('is_cancel', models.CharField(max_length=60, verbose_name='作废状态')),
                ('purchaser', models.CharField(max_length=60, verbose_name='采购组织')),
                ('status', models.CharField(max_length=60, verbose_name='单据状态')),
                ('demander', models.CharField(max_length=60, verbose_name='需求组织')),
                ('goods_id', models.CharField(max_length=60, verbose_name='物料编码')),
                ('goods_name', models.CharField(max_length=60, verbose_name='物料名称')),
                ('goods_size', models.CharField(max_length=60, verbose_name='规格型号')),
                ('goods_unit', models.CharField(max_length=60, verbose_name='库存单位')),
                ('quantity_receivable', models.IntegerField(default=0, verbose_name='应收数量')),
                ('quantity_received', models.IntegerField(verbose_name='实收数量')),
                ('batch_number', models.CharField(max_length=60, verbose_name='批号')),
                ('warehouse', models.CharField(max_length=60, verbose_name='仓库')),
                ('expiry_date', models.DateTimeField(max_length=60, verbose_name='有效期至')),
                ('produce_time', models.DateTimeField(max_length=60, verbose_name='生产日期')),
                ('memorandum', models.CharField(blank=True, max_length=60, null=True, verbose_name='备注')),
                ('origin_order_category', models.CharField(max_length=60, verbose_name='源单类型')),
                ('origin_order_id', models.CharField(max_length=60, verbose_name='源单编号')),
                ('payable_quantity', models.IntegerField(verbose_name='关联应付数量（计价基本）')),
                ('purchase_order_id', models.CharField(max_length=60, verbose_name='订单单号')),
                ('assist_quantity', models.IntegerField(verbose_name='实收数量(辅单位)')),
                ('multiple', models.IntegerField(verbose_name='主/辅换算率')),
                ('price', models.IntegerField(verbose_name='成本价')),
                ('storage', models.CharField(blank=True, max_length=60, null=True, verbose_name='仓位')),
                ('order_status', models.SmallIntegerField(choices=[(0, '已取消'), (1, '未递交'), (2, '已递交')], default=1, verbose_name='订单状态')),
                ('mistake_tag', models.SmallIntegerField(choices=[(0, '正常'), (1, '入库合并'), (2, '重复递交'), (3, '非法工厂'), (4, '非法货品'), (5, '非法仓库'), (6, '采购单错误')], default=0, verbose_name='错误标识')),
            ],
            options={
                'verbose_name': 'wms-s-原始入库单查询',
                'verbose_name_plural': 'wms-s-原始入库单查询',
                'db_table': 'wms_s_oristockin',
            },
        ),
        migrations.CreateModel(
            name='StockInInfo',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('create_time', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('update_time', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('is_delete', models.BooleanField(default=False, verbose_name='删除标记')),
                ('creator', models.CharField(blank=True, max_length=90, null=True, verbose_name='创建者')),
                ('order_category', models.CharField(max_length=60, verbose_name='单据类型')),
                ('to_organization', models.CharField(blank=True, max_length=60, null=True, verbose_name='对应组织')),
                ('order_creator', models.CharField(max_length=60, verbose_name='创建人')),
                ('supplier_address', models.CharField(blank=True, max_length=60, null=True, verbose_name='供货方地址')),
                ('create_date', models.DateTimeField(max_length=60, verbose_name='创建日期')),
                ('seller', models.CharField(max_length=60, verbose_name='结算方')),
                ('bs_category', models.CharField(max_length=60, verbose_name='业务类型')),
                ('stockin_order_id', models.CharField(max_length=60, verbose_name='单据编号')),
                ('last_modifier', models.CharField(max_length=60, verbose_name='最后修改人')),
                ('payee', models.CharField(max_length=60, verbose_name='收款方')),
                ('stockin_time', models.DateTimeField(max_length=60, verbose_name='入库日期')),
                ('last_modify_time', models.DateTimeField(max_length=60, verbose_name='最后修改日期')),
                ('consignee', models.CharField(max_length=60, verbose_name='收料组织')),
                ('is_cancel', models.CharField(max_length=60, verbose_name='作废状态')),
                ('purchaser', models.CharField(max_length=60, verbose_name='采购组织')),
                ('status', models.CharField(max_length=60, verbose_name='单据状态')),
                ('demander', models.CharField(max_length=60, verbose_name='需求组织')),
                ('goods_id', models.CharField(max_length=60, verbose_name='物料编码')),
                ('goods_size', models.CharField(max_length=60, verbose_name='规格型号')),
                ('goods_unit', models.CharField(max_length=60, verbose_name='库存单位')),
                ('quantity_receivable', models.IntegerField(blank=True, null=True, verbose_name='应收数量')),
                ('quantity_received', models.IntegerField(verbose_name='实收数量')),
                ('batch_number', models.CharField(max_length=60, verbose_name='批号')),
                ('expiry_date', models.DateTimeField(max_length=60, verbose_name='有效期至')),
                ('produce_time', models.DateTimeField(max_length=60, verbose_name='生产日期')),
                ('memorandum', models.CharField(blank=True, max_length=60, null=True, verbose_name='备注')),
                ('origin_order_category', models.CharField(max_length=60, verbose_name='源单类型')),
                ('origin_order_id', models.CharField(max_length=60, verbose_name='源单编号')),
                ('payable_quantity', models.IntegerField(verbose_name='关联应付数量（计价基本）')),
                ('assist_quantity', models.IntegerField(verbose_name='实收数量(辅单位)')),
                ('multiple', models.IntegerField(verbose_name='主/辅换算率')),
                ('price', models.IntegerField(verbose_name='成本价')),
                ('storage', models.CharField(blank=True, max_length=60, null=True, verbose_name='货位')),
                ('quantity_linking', models.IntegerField(default=0, verbose_name='关联存货数量')),
                ('order_status', models.SmallIntegerField(choices=[(0, '已取消'), (1, '未审核'), (2, '待核销'), (3, '已完成')], default=1, verbose_name='订单状态')),
                ('mistake_tag', models.SmallIntegerField(choices=[(0, '正常'), (1, '原始单缺漏'), (2, '货主错误'), (3, '仓库错误'), (4, '货品错误'), (5, '采购单错误'), (5, '采购单数量错误')], default=0, verbose_name='错误标识')),
                ('goods_name', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='goods.GoodsInfo', verbose_name='物料名称')),
                ('purchase_order_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='purchase.PurchaseInfo', verbose_name='订单单号')),
                ('supplier', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='company.CompanyInfo', verbose_name='供货方')),
                ('warehouse', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='warehouse.WarehouseInfo', verbose_name='仓库')),
            ],
            options={
                'verbose_name': 'wms-s-入库单查询',
                'verbose_name_plural': 'wms-s-入库单查询',
                'db_table': 'wms_s_stockin',
            },
        ),
        migrations.CreateModel(
            name='OriStockInPending',
            fields=[
            ],
            options={
                'verbose_name': 'wms-未递交原始入库单',
                'verbose_name_plural': 'wms-未递交原始入库单',
                'proxy': True,
                'indexes': [],
            },
            bases=('stockin.oristockininfo',),
        ),
        migrations.CreateModel(
            name='StockInPending',
            fields=[
            ],
            options={
                'verbose_name': 'wms-s-未审核入库单',
                'verbose_name_plural': 'wms-s-未审核入库单',
                'proxy': True,
                'indexes': [],
            },
            bases=('stockin.stockininfo',),
        ),
        migrations.AlterUniqueTogether(
            name='stockininfo',
            unique_together=set([('stockin_order_id', 'goods_id', 'warehouse', 'expiry_date')]),
        ),
    ]
