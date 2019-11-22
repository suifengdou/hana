# -*- coding: utf-8 -*-
# Generated by Django 1.11.16 on 2019-11-19 21:06
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='CompanyInfo',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('create_time', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('update_time', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('is_delete', models.BooleanField(default=False, verbose_name='删除标记')),
                ('creator', models.CharField(blank=True, max_length=90, null=True, verbose_name='创建者')),
                ('company_name', models.CharField(db_index=True, max_length=30, unique=True, verbose_name='公司简称')),
                ('company', models.CharField(blank=True, max_length=60, null=True, verbose_name='公司全称')),
                ('tax_fil_number', models.CharField(blank=True, max_length=30, null=True, unique=True, verbose_name='税号')),
                ('order_status', models.IntegerField(choices=[(0, '已取消'), (1, '正常')], default=1, verbose_name='状态')),
                ('category', models.IntegerField(choices=[(0, '本埠主体'), (1, '物流快递'), (2, '仓库存储'), (3, '生产制造'), (4, '其他类型')], default=1, verbose_name='公司类型')),
            ],
            options={
                'verbose_name': 'BASE-公司-公司管理',
                'verbose_name_plural': 'BASE-公司-公司管理',
                'db_table': 'base_company',
            },
        ),
        migrations.CreateModel(
            name='LogisticsInfo',
            fields=[
            ],
            options={
                'verbose_name': 'BASE-公司-快递物流',
                'verbose_name_plural': 'BASE-公司-快递物流',
                'proxy': True,
                'indexes': [],
            },
            bases=('company.companyinfo',),
        ),
        migrations.CreateModel(
            name='ManuInfo',
            fields=[
            ],
            options={
                'verbose_name': 'BASE-公司-生产制造',
                'verbose_name_plural': 'BASE-公司-生产制造',
                'proxy': True,
                'indexes': [],
            },
            bases=('company.companyinfo',),
        ),
        migrations.CreateModel(
            name='WareInfo',
            fields=[
            ],
            options={
                'verbose_name': 'BASE-公司-仓库存储',
                'verbose_name_plural': 'BASE-公司-仓库存储',
                'proxy': True,
                'indexes': [],
            },
            bases=('company.companyinfo',),
        ),
    ]
