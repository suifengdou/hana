# -*- coding: utf-8 -*-
# @Time    : 2019/11/25 20:21
# @Author  : Hann
# @Site    : 
# @File    : adminx.py
# @Software: PyCharm

from django.db import models

from db.base_model import BaseModel


class ChangeLogInfo(BaseModel):
    version_number = models.CharField(max_length=55, verbose_name='版本号')
    description = models.TextField(verbose_name='版本说明')

    class Meta:
        verbose_name = '版本说明'
        verbose_name_plural = verbose_name
        db_table = 'base_zoneu'

    def __str__(self):
        return self.version_number