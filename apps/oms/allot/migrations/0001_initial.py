# -*- coding: utf-8 -*-
# Generated by Django 1.11.25 on 2020-02-29 06:15
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('warehouse', '0001_initial'),
        ('stock', '0003_auto_20200229_1145'),
        ('goods', '0001_initial'),
        ('department', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='VAllotSIInfo',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('create_time', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('update_time', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('is_delete', models.BooleanField(default=False, verbose_name='删除标记')),
                ('creator', models.CharField(blank=True, max_length=90, null=True, verbose_name='创建者')),
                ('order_id', models.CharField(db_index=True, max_length=60, unique=True, verbose_name='单据编号')),
                ('order_category', models.SmallIntegerField(choices=[(0, '计划入库'), (1, '临时入库')], default=0, verbose_name='单据类型')),
                ('goods_id', models.CharField(db_index=True, max_length=60, verbose_name='物料编码')),
                ('quantity', models.IntegerField(verbose_name='入库数量')),
                ('memorandum', models.CharField(blank=True, max_length=300, null=True, verbose_name='备注')),
                ('order_status', models.SmallIntegerField(choices=[(0, '已取消'), (1, '未审核'), (2, '已完成')], db_index=True, default=1, verbose_name='订单状态')),
                ('mistake_tag', models.SmallIntegerField(choices=[(0, '正常'), (1, '未设置部门仓库'), (2, '多线程重复操作'), (3, '实仓实例保存错误'), (4, '部门仓实例保存错误')], default=0, verbose_name='错误标识')),
                ('department', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='department.DepartmentInfo', verbose_name='部门')),
                ('goods_name', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='goods.GoodsInfo', verbose_name='物料名称')),
                ('ori_department', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ori_dept', to='department.DepartmentInfo', verbose_name='源部门')),
                ('ori_vwarehouse', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ori_vware', to='warehouse.WarehouseVirtual', verbose_name='源部门仓')),
            ],
            options={
                'verbose_name': 'oms-部门入库单',
                'verbose_name_plural': 'oms-部门入库单',
                'db_table': 'oms_vallot_stockin',
            },
        ),
        migrations.CreateModel(
            name='VAllotSOInfo',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('create_time', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('update_time', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('is_delete', models.BooleanField(default=False, verbose_name='删除标记')),
                ('creator', models.CharField(blank=True, max_length=90, null=True, verbose_name='创建者')),
                ('order_id', models.CharField(max_length=50, unique=True, verbose_name='单据编号')),
                ('order_category', models.SmallIntegerField(choices=[(0, '计划出库'), (1, '临时出库')], default=0, verbose_name='单据类型')),
                ('goods_id', models.CharField(max_length=50, verbose_name='物料编码')),
                ('quantity', models.IntegerField(verbose_name='分配总量')),
                ('undistributed', models.IntegerField(verbose_name='待分配数量')),
                ('memorandum', models.CharField(blank=True, max_length=300, null=True, verbose_name='备注')),
                ('mistake_tag', models.SmallIntegerField(choices=[(0, '正常'), (1, '调拨数量不足'), (2, '更新虚拟库存错误'), (3, '单据保存出错'), (4, '保存部门仓失败'), (5, '保存实仓失败'), (6, '保存部门仓失败'), (7, '部门没有此货品')], default=0, verbose_name='错误原因')),
                ('order_status', models.SmallIntegerField(choices=[(0, '已取消'), (1, '待审核'), (2, '待分配'), (3, '已完成')], default=1, verbose_name='状态')),
                ('department', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='department.DepartmentInfo', verbose_name='部门')),
                ('dept_stock', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='stock.TransDeptStock', verbose_name='源部门仓')),
                ('goods_name', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='goods.GoodsInfo', verbose_name='物料名称')),
                ('vwarehouse', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='a_vware', to='warehouse.WarehouseVirtual', verbose_name='部门仓')),
                ('warehouse', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='a_ware', to='warehouse.WarehouseGeneral', verbose_name='仓库')),
            ],
            options={
                'verbose_name': 'oms-部门出库单',
                'verbose_name_plural': 'oms-部门出库单',
                'db_table': 'oms_vallot_stockout',
            },
        ),
        migrations.AddField(
            model_name='vallotsiinfo',
            name='va_stockin',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='allot.VAllotSOInfo', verbose_name='关联入库单'),
        ),
        migrations.AddField(
            model_name='vallotsiinfo',
            name='vwarehouse',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='asi_vware', to='warehouse.WarehouseVirtual', verbose_name='部门仓'),
        ),
        migrations.AddField(
            model_name='vallotsiinfo',
            name='warehouse',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='asi_ware', to='warehouse.WarehouseGeneral', verbose_name='仓库'),
        ),
        migrations.CreateModel(
            name='VASICheck',
            fields=[
            ],
            options={
                'verbose_name': 'oms-a-未审核部门入库单',
                'verbose_name_plural': 'oms-a-未审核部门入库单',
                'proxy': True,
                'indexes': [],
            },
            bases=('allot.vallotsoinfo',),
        ),
        migrations.CreateModel(
            name='VASOCheck',
            fields=[
            ],
            options={
                'verbose_name': 'oms-a-未审核部门出库单',
                'verbose_name_plural': 'oms-a-未审核部门出库单',
                'proxy': True,
                'indexes': [],
            },
            bases=('allot.vallotsoinfo',),
        ),
        migrations.CreateModel(
            name='VASOHandle',
            fields=[
            ],
            options={
                'verbose_name': 'oms-a-未分配部门出库单',
                'verbose_name_plural': 'oms-a-未分配部门出库单',
                'proxy': True,
                'indexes': [],
            },
            bases=('allot.vallotsoinfo',),
        ),
    ]