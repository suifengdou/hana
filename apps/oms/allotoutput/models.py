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
from apps.base.warehouse.models import WarehouseVirtual


class OutputInfo(BaseModel):

    order_category = models.CharField(max_length=30, verbose_name='单据类型')
    customer = models.CharField(max_length=50, verbose_name='客户')
    department = models.CharField(max_length=50, verbose_name='领料部门')
    consignor = models.CharField(max_length=50, verbose_name='货主')
    memo = models.CharField(max_length=300, verbose_name='备注')
    order_id = models.CharField(unique=True, max_length=60, verbose_name='单据编号')
    create_date = models.DateTimeField(max_length='日期')
    goods_id = models.CharField(max_length=60, verbose_name='物料编码', db_index=True)
    goods_name = models.CharField(max_length=60, verbose_name='物料名称')
    quantity = models.IntegerField(verbose_name='实发数量')
    warehouse = models.CharField(max_length=50, verbose_name='发货仓库')
    origin = models.CharField(blank=True, null=True, max_length=30, verbose_name='源单类型')
    origin_order_id = models.CharField(blank=True, null=True, max_length=50, verbose_name='源单编号')
    consignee = models.CharField(max_length=30, verbose_name='收货人')
    mobile = models.CharField(max_length=30, verbose_name='联系电话')
    address = models.CharField(max_length=200, verbose_name='收货地址')
    out_category = models.CharField(max_length=30, verbose_name='出库类型')

    class Meta:
        verbose_name = 'OMS-其他出库单查询'
        verbose_name_plural = verbose_name
        db_table = 'oms_a_output'

