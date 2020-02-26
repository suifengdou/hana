# -*- coding: utf-8 -*-
# Generated by Django 1.11.16 on 2020-02-26 13:59
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('department', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='QuotaDeInfo',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('create_time', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('update_time', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('is_delete', models.BooleanField(default=False, verbose_name='删除标记')),
                ('creator', models.CharField(blank=True, max_length=90, null=True, verbose_name='创建者')),
                ('quota_name', models.CharField(max_length=60, unique=True, verbose_name='额度名称')),
                ('quota', models.IntegerField(verbose_name='存货额度')),
                ('category', models.SmallIntegerField(choices=[(0, '常规'), (1, '临时')], default=0, verbose_name='类型')),
                ('order_status', models.SmallIntegerField(choices=[(0, '取消'), (1, '正常'), (2, '失效')], default=1, verbose_name='单据状态')),
                ('maturity', models.DateTimeField(verbose_name='到期日')),
                ('department', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='department.DepartmentInfo', verbose_name='部门')),
            ],
            options={
                'verbose_name': 'B-规则-部门限额查询',
                'verbose_name_plural': 'B-规则-部门限额查询',
                'db_table': 'base_rag_quota',
            },
        ),
        migrations.CreateModel(
            name='QuotaDeValidInfo',
            fields=[
            ],
            options={
                'verbose_name': 'B-规则-有效部门限额',
                'verbose_name_plural': 'B-规则-有效部门限额',
                'proxy': True,
                'indexes': [],
            },
            bases=('ragulation.quotadeinfo',),
        ),
    ]
