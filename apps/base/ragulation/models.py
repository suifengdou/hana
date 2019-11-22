# -*- coding: utf-8 -*-
# @Time    : 2019/11/19 20:14
# @Author  : Hann
# @Site    :
# @File    : adminx.py
# @Software: PyCharm

from db.base_model import BaseModel
from django.db import models

from apps.base.department.models import DepartmentInfo


class QuotaDeInfo(BaseModel):
    CATEGORY = (
        (0, '常规'),
        (1, '临时'),
    )
    ORDER_STATUS = (
        (0, '取消'),
        (1, '正常'),
        (2, '失效'),
    )

    quota_name = models.CharField(unique=True, max_length=60, verbose_name='额度名称')
    department = models.ForeignKey(DepartmentInfo, models.CASCADE, verbose_name='部门')
    quota = models.IntegerField(verbose_name='存货额度')
    category = models.SmallIntegerField(choices=CATEGORY, default=0, verbose_name='类型')
    order_status = models.SmallIntegerField(choices=ORDER_STATUS, default=1, verbose_name='单据状态')
    maturity = models.DateTimeField(verbose_name='到期日')

    class Meta:
        verbose_name = 'B-规则-部门限额查询'
        verbose_name_plural = verbose_name
        db_table = 'base_rag_quota'

    def __str__(self):
        return self.quota_name


class QuotaDeValidInfo(QuotaDeInfo):

    class Meta:
        verbose_name = 'B-规则-有效部门限额'
        verbose_name_plural = verbose_name
        proxy = True




