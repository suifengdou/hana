# -*- coding: utf-8 -*-
# Generated by Django 1.11.16 on 2019-11-19 21:06
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='BarCodeInfo',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('create_time', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('update_time', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('is_delete', models.BooleanField(default=False, verbose_name='删除标记')),
                ('creator', models.CharField(blank=True, max_length=90, null=True, verbose_name='创建者')),
                ('barcode', models.CharField(max_length=90, verbose_name='条码')),
                ('order_status', models.SmallIntegerField(choices=[(0, '取消'), (1, '正常')], default=1, verbose_name='条码状态')),
            ],
            options={
                'verbose_name': 'B-产品-条码',
                'verbose_name_plural': 'B-产品-条码',
                'db_table': 'base_goods_barcode',
            },
        ),
        migrations.CreateModel(
            name='GoodsInfo',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('create_time', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('update_time', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('is_delete', models.BooleanField(default=False, verbose_name='删除标记')),
                ('creator', models.CharField(blank=True, max_length=90, null=True, verbose_name='创建者')),
                ('goods_name', models.CharField(max_length=150, verbose_name='货品名称')),
                ('goods_id', models.CharField(max_length=150, unique=True, verbose_name='货品代码')),
                ('category', models.SmallIntegerField(choices=[(0, '膜'), (1, '水'), (2, '液'), (3, '霜'), (4, '膏'), (5, '粉')], default=0, verbose_name='类型')),
                ('e_name', models.CharField(max_length=200, verbose_name='英文名')),
                ('p_name', models.CharField(max_length=200, verbose_name='产地名')),
                ('price', models.IntegerField(verbose_name='单价')),
                ('logistics_time', models.IntegerField(verbose_name='物流周期（天）')),
                ('order_time', models.IntegerField(verbose_name='订货周期（天）')),
                ('memorandum', models.CharField(blank=True, max_length=360, null=True, verbose_name='备注')),
                ('order_status', models.SmallIntegerField(choices=[(0, '取消'), (1, '正常')], default=1, verbose_name='货品状态')),
                ('package_unit', models.IntegerField(blank=True, null=True, verbose_name='装箱规格')),
            ],
            options={
                'verbose_name': 'B-产品-货品',
                'verbose_name_plural': 'B-产品-货品',
                'db_table': 'base_goods_goods',
            },
        ),
        migrations.CreateModel(
            name='IPackagesInfo',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('create_time', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('update_time', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('is_delete', models.BooleanField(default=False, verbose_name='删除标记')),
                ('creator', models.CharField(blank=True, max_length=90, null=True, verbose_name='创建者')),
                ('p_name', models.CharField(max_length=50, unique=True, verbose_name='装箱内箱名称')),
                ('length', models.IntegerField(verbose_name='长')),
                ('width', models.IntegerField(verbose_name='宽')),
                ('height', models.IntegerField(verbose_name='高')),
                ('multiple', models.SmallIntegerField(verbose_name='包装倍数')),
                ('order_status', models.SmallIntegerField(choices=[(0, '取消'), (1, '正常')], default=1, verbose_name='内箱状态')),
            ],
            options={
                'verbose_name': 'B-产品-装箱内箱',
                'verbose_name_plural': 'B-产品-装箱内箱',
                'db_table': 'base_goods_ipackage',
            },
        ),
        migrations.CreateModel(
            name='OPackagesInfo',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('create_time', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('update_time', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('is_delete', models.BooleanField(default=False, verbose_name='删除标记')),
                ('creator', models.CharField(blank=True, max_length=90, null=True, verbose_name='创建者')),
                ('p_name', models.CharField(max_length=50, unique=True, verbose_name='装箱外箱名称')),
                ('length', models.IntegerField(verbose_name='长')),
                ('width', models.IntegerField(verbose_name='宽')),
                ('height', models.IntegerField(verbose_name='高')),
                ('order_status', models.SmallIntegerField(choices=[(0, '取消'), (1, '正常')], default=1, verbose_name='外箱状态')),
            ],
            options={
                'verbose_name': 'B-产品-装箱外箱',
                'verbose_name_plural': 'B-产品-装箱外箱',
                'db_table': 'base_goods_opackage',
            },
        ),
        migrations.CreateModel(
            name='SeriesInfo',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('create_time', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('update_time', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('is_delete', models.BooleanField(default=False, verbose_name='删除标记')),
                ('creator', models.CharField(blank=True, max_length=90, null=True, verbose_name='创建者')),
                ('s_name', models.CharField(max_length=100, unique=True, verbose_name='系列名称')),
                ('category', models.CharField(blank=True, max_length=100, null=True, verbose_name='系列类型')),
                ('order_status', models.SmallIntegerField(choices=[(0, '取消'), (1, '正常')], default=1, verbose_name='系列状态')),
            ],
            options={
                'verbose_name': 'B-产品-系列',
                'verbose_name_plural': 'B-产品-系列',
                'db_table': 'base_goods_series',
            },
        ),
        migrations.CreateModel(
            name='SizeInfo',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('create_time', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('update_time', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('is_delete', models.BooleanField(default=False, verbose_name='删除标记')),
                ('creator', models.CharField(blank=True, max_length=90, null=True, verbose_name='创建者')),
                ('s_name', models.CharField(max_length=50, unique=True, verbose_name='规格名称')),
                ('unit', models.CharField(max_length=50, verbose_name='度量单位')),
                ('value', models.IntegerField(verbose_name='数值')),
                ('multiple', models.IntegerField(verbose_name='最小包装数量')),
                ('multiple_unit', models.CharField(blank=True, max_length=50, null=True, verbose_name='倍数单位')),
                ('memorandum', models.CharField(blank=True, max_length=100, null=True, verbose_name='备注')),
                ('order_status', models.SmallIntegerField(choices=[(0, '取消'), (1, '正常')], default=1, verbose_name='规格状态')),
            ],
            options={
                'verbose_name': 'B-产品-规格',
                'verbose_name_plural': 'B-产品-规格',
                'db_table': 'base_goods_size',
            },
        ),
        migrations.AddField(
            model_name='goodsinfo',
            name='series',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='goods.SeriesInfo', verbose_name='系列'),
        ),
        migrations.AddField(
            model_name='goodsinfo',
            name='size',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='goods.SizeInfo', verbose_name='规格'),
        ),
        migrations.AlterUniqueTogether(
            name='goodsinfo',
            unique_together=set([('goods_name', 'size')]),
        ),
    ]