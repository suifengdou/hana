# @Site    :
# @File    :  models.py
# @Software:  PyCharm

from django.db import models
import django.utils.timezone as timezone
from django.db.models import Sum, Avg, Min, Max

import pandas as pd

from db.base_model import BaseModel


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



class MyDepartment(DepartmentInfo):

    class Meta:
        verbose_name = 'B-部门-本部门'
        verbose_name_plural = verbose_name
        proxy = True