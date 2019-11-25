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
        (0, '国内'),
        (1, '国际'),
    )

    name = models.CharField(unique=True, max_length=30, verbose_name='部门名称', db_index=True)
    order_status = models.IntegerField(choices=ORDER_STATUS, default=1, verbose_name='状态')
    category = models.IntegerField(choices=CATEGORY, default=1, verbose_name='部门类型')

    class Meta:
        verbose_name = 'B-本部门'
        verbose_name_plural = verbose_name
        db_table = 'base_department'

    def __str__(self):
        return self.name

    def quotavalid(self):
        quota = self.quotadeinfo_set.all().filter(order_status=1).aggregate(Sum("quota"))['quota__sum']
        if quota:
            return quota
        else:
            return 0
    quotavalid.short_description = '运维额度'


class DepartmentOperationInfo(DepartmentInfo):

    class Meta:
        verbose_name = 'B-部门查询'
        verbose_name_plural = verbose_name
        proxy = True