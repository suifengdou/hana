# -*- coding: utf-8 -*-
# @Time    : 2019/12/3 8:56
# @Author  : Hann
# @Site    : 
# @File    : adminx.py
# @Software: PyCharm

from django.db import models
import django.utils.timezone as timezone

from db.base_model import BaseModel
from apps.base.department.models import DepartmentInfo
from apps.base.goods.models import GoodsInfo


class DistributionInfo(BaseModel):

    ORDER_STATUS = (
        (0, '已取消'),
        (1, '未审核'),
        (2, '已审核'),
    )

    distribution_order_id = models.CharField(max_length=50, verbose_name='分配单号')
    department = models.ForeignKey(DepartmentInfo, on_delete=models.CASCADE, verbose_name='部门')
    goods_name = models.ForeignKey(GoodsInfo, on_delete=models.CASCADE, verbose_name='货品名称')
    quantity = models.IntegerField(verbose_name='分配数量')
    memorandum = models.CharField(null=True, blank=True, max_length=200, verbose_name='备注')

    class Meta:
        verbose_name = 'OMS-预分配'
        verbose_name_plural = verbose_name
        db_table = 'oms_pdb_distribution'

