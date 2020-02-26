# -*- coding: utf-8 -*-
# Generated by Django 1.11.16 on 2020-02-26 13:59
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='OirLoss',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('create_time', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('update_time', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('is_delete', models.BooleanField(default=False, verbose_name='删除标记')),
                ('creator', models.CharField(blank=True, max_length=90, null=True, verbose_name='创建者')),
                ('detail_num', models.CharField(db_index=True, max_length=20, verbose_name='明细信息行号')),
                ('order_id', models.CharField(db_index=True, max_length=60, verbose_name='单据编号')),
                ('order_category', models.CharField(max_length=60, verbose_name='单据类型')),
                ('date', models.DateTimeField(max_length=60, verbose_name='日期')),
                ('ori_creator', models.CharField(max_length=60, verbose_name='创建人')),
                ('owner', models.CharField(max_length=50, verbose_name='货主')),
                ('memorandum', models.CharField(blank=True, max_length=200, null=True, verbose_name='备注')),
                ('goods_id', models.CharField(db_index=True, max_length=60, verbose_name='物料编码')),
                ('goods_name', models.CharField(max_length=60, verbose_name='物料名称')),
                ('goods_size', models.CharField(max_length=60, verbose_name='规格型号')),
                ('stock', models.IntegerField(verbose_name='账存数量')),
                ('check', models.IntegerField(verbose_name='盘点数量')),
                ('quantity', models.IntegerField(verbose_name='盘亏数量')),
                ('warehouse', models.CharField(db_index=True, max_length=60, verbose_name='仓库')),
                ('batch_num', models.CharField(max_length=60, verbose_name='批号')),
                ('produce_date', models.DateTimeField(max_length=60, verbose_name='生产日期')),
                ('expiry_date', models.DateTimeField(max_length=60, verbose_name='到期日')),
                ('order_status', models.SmallIntegerField(choices=[(0, '已取消'), (1, '未递交'), (2, '已递交')], default=1, verbose_name='状态')),
                ('mistake_tag', models.SmallIntegerField(choices=[(0, '正常'), (1, '重复递交'), (2, '部门非法'), (3, '货品非法'), (4, '仓库非法'), (5, '实例存储失败')], default=0, verbose_name='问题原因')),
            ],
            options={
                'verbose_name': 'oms-原始盘亏单',
                'verbose_name_plural': 'oms-原始盘亏单',
                'db_table': 'oms_ic_oriloss',
            },
        ),
        migrations.CreateModel(
            name='OriAllocation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('create_time', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('update_time', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('is_delete', models.BooleanField(default=False, verbose_name='删除标记')),
                ('creator', models.CharField(blank=True, max_length=90, null=True, verbose_name='创建者')),
                ('detail_num', models.CharField(db_index=True, max_length=20, verbose_name='明细信息行号')),
                ('order_id', models.CharField(db_index=True, max_length=60, verbose_name='单据编号')),
                ('order_category', models.CharField(max_length=60, verbose_name='单据类型')),
                ('trans_in', models.CharField(max_length=50, verbose_name='调入库存组织')),
                ('date', models.DateTimeField(max_length=60, verbose_name='日期')),
                ('trans_out', models.CharField(max_length=50, verbose_name='调出库存组织')),
                ('department', models.CharField(max_length=30, verbose_name='销售部门')),
                ('memorandum', models.CharField(blank=True, max_length=200, null=True, verbose_name='备注')),
                ('ori_creator', models.CharField(max_length=60, verbose_name='创建人')),
                ('goods_id', models.CharField(db_index=True, max_length=60, verbose_name='物料编码')),
                ('goods_name', models.CharField(max_length=60, verbose_name='物料名称')),
                ('goods_size', models.CharField(max_length=60, verbose_name='规格型号')),
                ('batch_num', models.CharField(max_length=60, verbose_name='批号')),
                ('quantity', models.IntegerField(verbose_name='调拨数量')),
                ('warehouse_out', models.CharField(db_index=True, max_length=60, verbose_name='调出仓库')),
                ('warehouse_in', models.CharField(db_index=True, max_length=60, verbose_name='调入仓库')),
                ('produce_date', models.DateTimeField(max_length=60, verbose_name='生产日期')),
                ('expiry_date', models.DateTimeField(max_length=60, verbose_name='有效期至')),
                ('stockin_date', models.DateTimeField(max_length=60, verbose_name='入库日期')),
                ('customer', models.CharField(max_length=50, verbose_name='客户')),
                ('order_status', models.SmallIntegerField(choices=[(0, '已取消'), (1, '未递交'), (2, '已递交')], default=1, verbose_name='状态')),
                ('mistake_tag', models.SmallIntegerField(choices=[(0, '正常'), (1, '重复递交'), (2, '供货商非法'), (3, '部门非法'), (4, '货品非法'), (5, '仓库非法'), (6, '实例保存错误')], default=0, verbose_name='问题原因')),
            ],
            options={
                'verbose_name': 'oms-原始直接调拨单',
                'verbose_name_plural': 'oms-原始直接调拨单',
                'db_table': 'oms_ic_oriallocation',
            },
        ),
        migrations.CreateModel(
            name='OriNPStockIn',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('create_time', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('update_time', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('is_delete', models.BooleanField(default=False, verbose_name='删除标记')),
                ('creator', models.CharField(blank=True, max_length=90, null=True, verbose_name='创建者')),
                ('detail_num', models.CharField(db_index=True, max_length=20, verbose_name='明细信息行号')),
                ('order_id', models.CharField(db_index=True, max_length=60, verbose_name='单据编号')),
                ('order_category', models.CharField(blank=True, max_length=60, null=True, verbose_name='单据类型')),
                ('ori_creator', models.CharField(blank=True, max_length=60, null=True, verbose_name='创建人')),
                ('department', models.CharField(max_length=30, verbose_name='部门')),
                ('owner', models.CharField(max_length=50, verbose_name='货主')),
                ('date', models.DateTimeField(max_length=60, verbose_name='日期')),
                ('goods_id', models.CharField(db_index=True, max_length=60, verbose_name='物料编码')),
                ('goods_name', models.CharField(max_length=60, verbose_name='物料名称')),
                ('goods_size', models.CharField(max_length=60, verbose_name='规格型号')),
                ('quantity', models.IntegerField(verbose_name='实收数量')),
                ('batch_number', models.CharField(max_length=60, verbose_name='批号')),
                ('warehouse', models.CharField(db_index=True, max_length=60, verbose_name='仓库')),
                ('expiry_date', models.DateTimeField(max_length=60, verbose_name='有效期至')),
                ('produce_date', models.DateTimeField(max_length=60, verbose_name='生产日期')),
                ('memorandum', models.CharField(blank=True, max_length=200, null=True, verbose_name='备注')),
                ('in_category', models.CharField(max_length=30, verbose_name='入库类型')),
                ('order_status', models.SmallIntegerField(choices=[(0, '已取消'), (1, '未递交'), (2, '已递交')], default=1, verbose_name='状态')),
                ('mistake_tag', models.SmallIntegerField(choices=[(0, '正常'), (1, '重复递交'), (2, '供货商非法'), (3, '部门非法'), (4, '货品非法'), (5, '仓库非法'), (6, '实例保存错误')], default=0, verbose_name='问题原因')),
            ],
            options={
                'verbose_name': 'oms-原始其他入库单',
                'verbose_name_plural': 'oms-原始其他入库单',
                'db_table': 'oms_ic_orinonpurstockin',
            },
        ),
        migrations.CreateModel(
            name='OriNSStockout',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('create_time', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('update_time', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('is_delete', models.BooleanField(default=False, verbose_name='删除标记')),
                ('creator', models.CharField(blank=True, max_length=90, null=True, verbose_name='创建者')),
                ('detail_num', models.CharField(max_length=20, verbose_name='明细信息行号')),
                ('order_category', models.CharField(max_length=30, verbose_name='单据类型')),
                ('customer', models.CharField(blank=True, max_length=50, null=True, verbose_name='客户')),
                ('department', models.CharField(max_length=50, verbose_name='领料部门')),
                ('owner', models.CharField(max_length=50, verbose_name='货主')),
                ('memorandum', models.CharField(blank=True, max_length=200, null=True, verbose_name='备注')),
                ('order_id', models.CharField(db_index=True, max_length=60, verbose_name='单据编号')),
                ('ori_creator', models.CharField(max_length=30, verbose_name='创建人')),
                ('date', models.DateTimeField(max_length='日期')),
                ('goods_id', models.CharField(db_index=True, max_length=60, verbose_name='物料编码')),
                ('goods_name', models.CharField(max_length=60, verbose_name='物料名称')),
                ('goods_size', models.CharField(blank=True, max_length=30, null=True, verbose_name='规格型号')),
                ('quantity', models.IntegerField(verbose_name='实发数量')),
                ('warehouse', models.CharField(max_length=50, verbose_name='发货仓库')),
                ('store_id', models.CharField(max_length=30, verbose_name='店号')),
                ('buyer', models.CharField(max_length=30, verbose_name='收货人')),
                ('smartphone', models.CharField(max_length=30, verbose_name='联系电话')),
                ('address', models.CharField(max_length=200, verbose_name='收货地址')),
                ('out_category', models.CharField(max_length=30, verbose_name='出库类型')),
                ('order_status', models.SmallIntegerField(choices=[(0, '已取消'), (1, '未递交'), (2, '已递交')], default=1, verbose_name='状态')),
                ('mistake_tag', models.SmallIntegerField(choices=[(0, '正常'), (1, '导入重复'), (2, '部门非法'), (3, '货品非法'), (4, '仓库非法'), (5, '实例保存错误')], default=0, verbose_name='问题原因')),
            ],
            options={
                'verbose_name': 'oms-原始其他出库单',
                'verbose_name_plural': 'oms-原始其他出库单',
                'db_table': 'oms_ic_orinonsalestockout',
            },
        ),
        migrations.CreateModel(
            name='OriPurchaseInfo',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('create_time', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('update_time', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('is_delete', models.BooleanField(default=False, verbose_name='删除标记')),
                ('creator', models.CharField(blank=True, max_length=90, null=True, verbose_name='创建者')),
                ('detail_num', models.CharField(max_length=20, verbose_name='明细信息行号')),
                ('order_id', models.CharField(max_length=50, verbose_name='单据编号')),
                ('purchase_time', models.DateTimeField(max_length=50, verbose_name='采购时间')),
                ('supplier', models.CharField(max_length=70, verbose_name='供应商')),
                ('status', models.CharField(max_length=50, verbose_name='单据状态')),
                ('puchaser', models.CharField(max_length=60, verbose_name='采购组织')),
                ('is_cancel', models.CharField(max_length=50, verbose_name='关闭状态')),
                ('goods_unit', models.CharField(max_length=50, verbose_name='采购单位')),
                ('quantity', models.IntegerField(verbose_name='采购数量')),
                ('delivery_date', models.DateTimeField(verbose_name='交货日期')),
                ('price', models.FloatField(verbose_name='含税单价')),
                ('goods_id', models.CharField(db_index=True, max_length=60, verbose_name='物料编码')),
                ('goods_name', models.CharField(max_length=60, verbose_name='物料名称')),
                ('is_gift', models.CharField(max_length=50, verbose_name='是否赠品')),
                ('is_close', models.CharField(max_length=50, verbose_name='业务关闭')),
                ('order_status', models.SmallIntegerField(choices=[(0, '已取消'), (1, '未递交'), (2, '已递交')], default=1, verbose_name='状态')),
                ('mistake_tag', models.SmallIntegerField(choices=[(0, '正常'), (1, '重复递交'), (2, '工厂非法'), (3, '货品非法'), (4, '递交失败'), (5, '其他错误')], default=0, verbose_name='问题原因')),
            ],
            options={
                'verbose_name': 'oms-原始采购单',
                'verbose_name_plural': 'oms-原始采购单',
                'db_table': 'oms_ic_oripurchase',
            },
        ),
        migrations.CreateModel(
            name='OriPurRefund',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('create_time', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('update_time', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('is_delete', models.BooleanField(default=False, verbose_name='删除标记')),
                ('creator', models.CharField(blank=True, max_length=90, null=True, verbose_name='创建者')),
                ('detail_num', models.CharField(db_index=True, max_length=20, verbose_name='明细信息行号')),
                ('order_category', models.CharField(max_length=60, verbose_name='单据类型')),
                ('ori_creator', models.CharField(max_length=60, verbose_name='创建人')),
                ('order_id', models.CharField(db_index=True, max_length=60, verbose_name='单据编号')),
                ('date', models.DateTimeField(max_length=60, verbose_name='日期')),
                ('owner', models.CharField(max_length=50, verbose_name='货主')),
                ('department', models.CharField(max_length=30, verbose_name='销售部门')),
                ('goods_id', models.CharField(db_index=True, max_length=60, verbose_name='物料编码')),
                ('goods_name', models.CharField(max_length=60, verbose_name='物料名称')),
                ('goods_memo', models.CharField(max_length=200, verbose_name='物料说明')),
                ('batch_num', models.CharField(max_length=60, verbose_name='批号')),
                ('quantity', models.IntegerField(verbose_name='实退数量')),
                ('warehouse', models.CharField(db_index=True, max_length=60, verbose_name='仓库')),
                ('memorandum', models.CharField(blank=True, max_length=200, null=True, verbose_name='备注')),
                ('price', models.FloatField(verbose_name='单价')),
                ('amount', models.FloatField(verbose_name='价税合计')),
                ('order_status', models.SmallIntegerField(choices=[(0, '已取消'), (1, '未递交'), (2, '已递交')], default=1, verbose_name='状态')),
                ('mistake_tag', models.SmallIntegerField(choices=[(0, '正常'), (1, '导入重复'), (2, '部门非法'), (3, '货品非法'), (4, '仓库非法'), (5, '实例保存错误')], default=0, verbose_name='问题原因')),
            ],
            options={
                'verbose_name': 'oms-原始采购退料单',
                'verbose_name_plural': 'oms-原始采购退料单',
                'db_table': 'oms_ic_oripurrefund',
            },
        ),
        migrations.CreateModel(
            name='OriRefund',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('create_time', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('update_time', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('is_delete', models.BooleanField(default=False, verbose_name='删除标记')),
                ('creator', models.CharField(blank=True, max_length=90, null=True, verbose_name='创建者')),
                ('detail_num', models.CharField(db_index=True, max_length=20, verbose_name='明细信息行号')),
                ('order_id', models.CharField(db_index=True, max_length=60, verbose_name='单据编号')),
                ('order_category', models.CharField(max_length=60, verbose_name='单据类型')),
                ('ori_creator', models.CharField(max_length=60, verbose_name='创建人')),
                ('department', models.CharField(max_length=30, verbose_name='销售部门')),
                ('owner', models.CharField(max_length=50, verbose_name='货主')),
                ('date', models.DateTimeField(max_length=60, verbose_name='日期')),
                ('customer', models.CharField(max_length=60, verbose_name='退货客户')),
                ('memorandum', models.CharField(blank=True, max_length=200, null=True, verbose_name='备注')),
                ('buyer', models.CharField(max_length=50, verbose_name='收货方')),
                ('goods_id', models.CharField(db_index=True, max_length=60, verbose_name='物料编码')),
                ('goods_name', models.CharField(max_length=60, verbose_name='物料名称')),
                ('goods_size', models.CharField(max_length=60, verbose_name='规格型号')),
                ('quantity', models.IntegerField(verbose_name='实退数量')),
                ('refund_date', models.DateTimeField(max_length=60, verbose_name='退货日期')),
                ('batch_number', models.CharField(max_length=60, verbose_name='批号')),
                ('warehouse', models.CharField(db_index=True, max_length=60, verbose_name='仓库')),
                ('expiry_date', models.DateTimeField(max_length=60, verbose_name='有效期至')),
                ('produce_date', models.DateTimeField(max_length=60, verbose_name='生产日期')),
                ('price', models.FloatField(verbose_name='含税单价')),
                ('refund_information', models.CharField(blank=True, max_length=150, null=True, verbose_name='退货单号')),
                ('amount', models.FloatField(verbose_name='价税合计')),
                ('order_status', models.SmallIntegerField(choices=[(0, '已取消'), (1, '未递交'), (2, '已递交')], default=1, verbose_name='状态')),
                ('mistake_tag', models.SmallIntegerField(choices=[(0, '正常'), (1, '重复递交'), (2, '供货商非法'), (3, '部门非法'), (4, '货品非法'), (5, '仓库非法'), (6, '实例保存错误')], default=0, verbose_name='问题原因')),
            ],
            options={
                'verbose_name': 'oms-原始销售退货单',
                'verbose_name_plural': 'oms-原始销售退货单',
                'db_table': 'oms_ic_orirefund',
            },
        ),
        migrations.CreateModel(
            name='OriStockInInfo',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('create_time', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('update_time', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('is_delete', models.BooleanField(default=False, verbose_name='删除标记')),
                ('creator', models.CharField(blank=True, max_length=90, null=True, verbose_name='创建者')),
                ('detail_num', models.CharField(max_length=20, verbose_name='明细信息行号')),
                ('order_category', models.CharField(max_length=60, verbose_name='单据类型')),
                ('ori_creator', models.CharField(max_length=60, verbose_name='创建人')),
                ('supplier', models.CharField(max_length=60, verbose_name='供货方')),
                ('create_date', models.DateTimeField(max_length=60, verbose_name='创建日期')),
                ('seller', models.CharField(max_length=60, verbose_name='结算方')),
                ('bs_category', models.CharField(max_length=60, verbose_name='业务类型')),
                ('order_id', models.CharField(db_index=True, max_length=60, verbose_name='单据编号')),
                ('last_modifier', models.CharField(max_length=60, verbose_name='最后修改人')),
                ('payee', models.CharField(max_length=60, verbose_name='收款方')),
                ('stockin_date', models.DateTimeField(max_length=60, verbose_name='入库日期')),
                ('last_modify_time', models.DateTimeField(max_length=60, verbose_name='最后修改日期')),
                ('purchaser', models.CharField(max_length=60, verbose_name='采购组织')),
                ('department', models.CharField(max_length=60, verbose_name='收料部门')),
                ('goods_id', models.CharField(db_index=True, max_length=60, verbose_name='物料编码')),
                ('goods_name', models.CharField(max_length=60, verbose_name='物料名称')),
                ('goods_size', models.CharField(max_length=60, verbose_name='规格型号')),
                ('goods_unit', models.CharField(max_length=60, verbose_name='库存单位')),
                ('quantity_receivable', models.IntegerField(default=0, verbose_name='应收数量')),
                ('quantity_received', models.IntegerField(verbose_name='实收数量')),
                ('batch_number', models.CharField(blank=True, max_length=60, null=True, verbose_name='批号')),
                ('warehouse', models.CharField(db_index=True, max_length=60, verbose_name='仓库')),
                ('expiry_date', models.DateTimeField(blank=True, max_length=60, null=True, verbose_name='有效期至')),
                ('produce_date', models.DateTimeField(blank=True, max_length=60, null=True, verbose_name='生产日期')),
                ('memorandum', models.CharField(blank=True, max_length=200, null=True, verbose_name='备注')),
                ('origin_order_category', models.CharField(max_length=60, verbose_name='源单类型')),
                ('origin_order_id', models.CharField(max_length=60, verbose_name='源单编号')),
                ('purchase_order_id', models.CharField(blank=True, max_length=60, null=True, verbose_name='订单单号')),
                ('multiple', models.IntegerField(blank=True, null=True, verbose_name='主/辅换算率')),
                ('price', models.IntegerField(verbose_name='成本价')),
                ('storage', models.CharField(blank=True, max_length=60, null=True, verbose_name='仓位')),
                ('related_quantity', models.IntegerField(default=0, verbose_name='关联数量')),
                ('order_status', models.SmallIntegerField(choices=[(0, '已取消'), (1, '未递交'), (2, '已递交')], db_index=True, default=1, verbose_name='订单状态')),
                ('mistake_tag', models.SmallIntegerField(choices=[(0, '正常'), (1, '重复递交'), (2, '供货商非法'), (3, '部门非法'), (4, '货品非法'), (5, '仓库非法'), (6, '实例保存错误')], default=0, verbose_name='错误标识')),
            ],
            options={
                'verbose_name': 'wms-原始采购入库单',
                'verbose_name_plural': 'wms-原始采购入库单',
                'db_table': 'oms_ic_oristockin',
            },
        ),
        migrations.CreateModel(
            name='OriStockOut',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('create_time', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('update_time', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('is_delete', models.BooleanField(default=False, verbose_name='删除标记')),
                ('creator', models.CharField(blank=True, max_length=90, null=True, verbose_name='创建者')),
                ('detail_num', models.CharField(max_length=20, verbose_name='明细信息行号')),
                ('order_id', models.CharField(max_length=30, verbose_name='单据编号')),
                ('customer', models.CharField(max_length=60, verbose_name='客户')),
                ('ori_order_status', models.CharField(max_length=20, verbose_name='单据状态')),
                ('order_category', models.CharField(max_length=20, verbose_name='单据类型')),
                ('sale_organization', models.CharField(max_length=30, verbose_name='销售组织')),
                ('department', models.CharField(max_length=30, verbose_name='销售部门')),
                ('memorandum', models.CharField(blank=True, max_length=200, null=True, verbose_name='备注')),
                ('ori_creator', models.CharField(max_length=30, verbose_name='创建人')),
                ('date', models.DateTimeField(verbose_name='日期')),
                ('goods_id', models.CharField(max_length=50, verbose_name='物料编码')),
                ('goods_name', models.CharField(max_length=60, verbose_name='物料名称')),
                ('goods_size', models.CharField(max_length=50, verbose_name='规格型号')),
                ('quantity', models.IntegerField(verbose_name='实发数量')),
                ('warehouse', models.CharField(max_length=50, verbose_name='仓库')),
                ('price', models.FloatField(verbose_name='含税单价')),
                ('amount', models.FloatField(verbose_name='价税合计')),
                ('package_size', models.IntegerField(blank=True, null=True, verbose_name='主辅换算率')),
                ('buyer', models.CharField(blank=True, max_length=60, null=True, verbose_name='收货方')),
                ('address', models.CharField(blank=True, max_length=240, null=True, verbose_name='收货方地址')),
                ('mistake_tag', models.SmallIntegerField(choices=[(0, '正常'), (1, '导入重复'), (2, '部门非法'), (3, '货品非法'), (4, '仓库非法'), (5, '实例保存错误')], default=0, verbose_name='错误原因')),
                ('order_status', models.SmallIntegerField(choices=[(0, '已取消'), (1, '待递交'), (2, '已完成')], default=1, verbose_name='状态')),
            ],
            options={
                'verbose_name': 'wms-原始销售出库单查询',
                'verbose_name_plural': 'wms-原始销售出库单查询',
                'db_table': 'oms_ic_oristockout',
            },
        ),
        migrations.CreateModel(
            name='OriSurplus',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('create_time', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('update_time', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('is_delete', models.BooleanField(default=False, verbose_name='删除标记')),
                ('creator', models.CharField(blank=True, max_length=90, null=True, verbose_name='创建者')),
                ('detail_num', models.CharField(db_index=True, max_length=20, verbose_name='明细信息行号')),
                ('order_id', models.CharField(db_index=True, max_length=60, verbose_name='单据编号')),
                ('order_category', models.CharField(max_length=60, verbose_name='单据类型')),
                ('date', models.DateTimeField(max_length=60, verbose_name='日期')),
                ('ori_creator', models.CharField(max_length=60, verbose_name='创建人')),
                ('owner', models.CharField(max_length=50, verbose_name='货主')),
                ('memorandum', models.CharField(blank=True, max_length=200, null=True, verbose_name='备注')),
                ('goods_id', models.CharField(db_index=True, max_length=60, verbose_name='物料编码')),
                ('goods_name', models.CharField(max_length=60, verbose_name='物料名称')),
                ('goods_size', models.CharField(max_length=60, verbose_name='规格型号')),
                ('stock', models.IntegerField(verbose_name='账存数量')),
                ('check', models.IntegerField(verbose_name='盘点数量')),
                ('quantity', models.IntegerField(verbose_name='盘盈数量')),
                ('warehouse', models.CharField(db_index=True, max_length=60, verbose_name='仓库')),
                ('batch_num', models.CharField(max_length=60, verbose_name='批号')),
                ('produce_date', models.DateTimeField(max_length=60, verbose_name='生产日期')),
                ('expiry_date', models.DateTimeField(max_length=60, verbose_name='到期日')),
                ('order_status', models.SmallIntegerField(choices=[(0, '已取消'), (1, '未递交'), (2, '已递交')], default=1, verbose_name='状态')),
                ('mistake_tag', models.SmallIntegerField(choices=[(0, '正常'), (1, '重复递交'), (2, '供货商非法'), (3, '部门非法'), (4, '货品非法'), (5, '仓库非法'), (6, '实例保存错误')], default=0, verbose_name='问题原因')),
            ],
            options={
                'verbose_name': 'oms-原始盘盈单',
                'verbose_name_plural': 'oms-原始盘盈单',
                'db_table': 'oms_ic_orisurplus',
            },
        ),
        migrations.AlterUniqueTogether(
            name='orisurplus',
            unique_together=set([('detail_num', 'order_id')]),
        ),
        migrations.AlterUniqueTogether(
            name='oristockout',
            unique_together=set([('detail_num', 'order_id')]),
        ),
        migrations.AlterUniqueTogether(
            name='orirefund',
            unique_together=set([('detail_num', 'order_id')]),
        ),
        migrations.AlterUniqueTogether(
            name='oripurrefund',
            unique_together=set([('detail_num', 'order_id')]),
        ),
        migrations.AlterUniqueTogether(
            name='oripurchaseinfo',
            unique_together=set([('detail_num', 'order_id')]),
        ),
        migrations.AlterUniqueTogether(
            name='orinsstockout',
            unique_together=set([('detail_num', 'order_id')]),
        ),
        migrations.AlterUniqueTogether(
            name='orinpstockin',
            unique_together=set([('detail_num', 'order_id')]),
        ),
        migrations.AlterUniqueTogether(
            name='oriallocation',
            unique_together=set([('detail_num', 'order_id')]),
        ),
        migrations.AlterUniqueTogether(
            name='oirloss',
            unique_together=set([('detail_num', 'order_id')]),
        ),
        migrations.CreateModel(
            name='OriALUnhandle',
            fields=[
            ],
            options={
                'verbose_name': 'oms-原始未递交直接调拨单',
                'verbose_name_plural': 'oms-原始未递交直接调拨单',
                'proxy': True,
                'indexes': [],
            },
            bases=('import_console.oriallocation',),
        ),
        migrations.CreateModel(
            name='OriLOUnhandle',
            fields=[
            ],
            options={
                'verbose_name': 'oms-原始未递交盘亏单',
                'verbose_name_plural': 'oms-原始未递交盘亏单',
                'proxy': True,
                'indexes': [],
            },
            bases=('import_console.oirloss',),
        ),
        migrations.CreateModel(
            name='OriNPSIUnhandle',
            fields=[
            ],
            options={
                'verbose_name': 'oms-原始未递交其他入库单',
                'verbose_name_plural': 'oms-原始未递交其他入库单',
                'proxy': True,
                'indexes': [],
            },
            bases=('import_console.orinpstockin',),
        ),
        migrations.CreateModel(
            name='OriNSSOUnhandle',
            fields=[
            ],
            options={
                'verbose_name': 'oms-原始未递交其他出库单',
                'verbose_name_plural': 'oms-原始未递交其他出库单',
                'proxy': True,
                'indexes': [],
            },
            bases=('import_console.orinsstockout',),
        ),
        migrations.CreateModel(
            name='OriPRUnhandle',
            fields=[
            ],
            options={
                'verbose_name': 'oms-原始未递交采购退料单',
                'verbose_name_plural': 'oms-原始未递交采购退料单',
                'proxy': True,
                'indexes': [],
            },
            bases=('import_console.oripurrefund',),
        ),
        migrations.CreateModel(
            name='OriPurchaseUnhandle',
            fields=[
            ],
            options={
                'verbose_name': 'oms-未审核原始采购单',
                'verbose_name_plural': 'oms-未审核原始采购单',
                'proxy': True,
                'indexes': [],
            },
            bases=('import_console.oripurchaseinfo',),
        ),
        migrations.CreateModel(
            name='OriRefundUnhandle',
            fields=[
            ],
            options={
                'verbose_name': 'oms-原始未递交销售退货单',
                'verbose_name_plural': 'oms-原始未递交销售退货单',
                'proxy': True,
                'indexes': [],
            },
            bases=('import_console.orirefund',),
        ),
        migrations.CreateModel(
            name='OriStockInUnhandle',
            fields=[
            ],
            options={
                'verbose_name': 'wms-原始采购入库单未递交',
                'verbose_name_plural': 'wms-原始采购入库单未递交',
                'proxy': True,
                'indexes': [],
            },
            bases=('import_console.oristockininfo',),
        ),
        migrations.CreateModel(
            name='OriStockOutUnhandle',
            fields=[
            ],
            options={
                'verbose_name': 'wms-原始销售出库单未递交',
                'verbose_name_plural': 'wms-原始销售出库单未递交',
                'proxy': True,
                'indexes': [],
            },
            bases=('import_console.oristockout',),
        ),
        migrations.CreateModel(
            name='OriSUUnhandle',
            fields=[
            ],
            options={
                'verbose_name': 'oms-原始未递交盘盈单',
                'verbose_name_plural': 'oms-原始未递交盘盈单',
                'proxy': True,
                'indexes': [],
            },
            bases=('import_console.orisurplus',),
        ),
    ]
