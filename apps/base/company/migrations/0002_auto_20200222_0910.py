# -*- coding: utf-8 -*-
# Generated by Django 1.11.25 on 2020-02-22 09:10
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('company', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='companyinfo',
            name='company_name',
            field=models.CharField(db_index=True, max_length=100, unique=True, verbose_name='公司简称'),
        ),
    ]
