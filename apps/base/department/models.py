# @Site    :
# @File    :  models.py
# @Software:  PyCharm

from django.db import models
import django.utils.timezone as timezone
from django.db.models import Sum, Avg, Min, Max

import pandas as pd

from db.base_model import BaseModel


class CentreInfo(BaseModel):
    ORDER_STATUS = (
        (0, '已取消'),
        (1, '正常'),
    )
    CATEGORY = (
        (0, '独立'),
        (1, '全局'),
    )

    name = models.CharField(unique=True, max_length=150, verbose_name='中心名称', db_index=True)
    category = models.SmallIntegerField(choices=CATEGORY, default=0, verbose_name='类型')
    order_status = models.IntegerField(choices=ORDER_STATUS, default=1, verbose_name='状态')

    class Meta:
        verbose_name = 'B-部门-中心列表'
        verbose_name_plural = verbose_name
        db_table = 'base_centre'

    def __str__(self):
        return self.name


class DepartmentInfo(BaseModel):
    ORDER_STATUS = (
        (0, '已取消'),
        (1, '正常'),
    )
    CATEGORY = (
        (0, '独立'),
        (1, '全局'),
    )

    name = models.CharField(unique=True, max_length=150, verbose_name='部门名称', db_index=True)
    order_status = models.IntegerField(choices=ORDER_STATUS, default=1, verbose_name='状态')
    category = models.IntegerField(choices=CATEGORY, default=0, verbose_name='部门类型')
    department_id = models.CharField(null=True, blank=True, max_length=60, verbose_name='部门ID')
    centre = models.ForeignKey(CentreInfo, on_delete=models.CASCADE, null=True, blank=True, verbose_name='所属中心')

    class Meta:
        verbose_name = 'B-部门-部门列表'
        verbose_name_plural = verbose_name
        db_table = 'base_department'

    def __str__(self):
        return self.name

    @classmethod
    def verify_mandatory(cls, columns_key):
        VERIFY_FIELD = ['name']

        for i in VERIFY_FIELD:
            if i not in columns_key:
                return 'verify_field error, must have mandatory field: "{}""'.format(i)
        else:
            return None
