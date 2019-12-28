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
from apps.base.warehouse.models import WarehouseGeneral, WarehouseVirtual



class VirtualAllot(BaseModel):
    CATEGORY = (
        (0, '有借无还'),
        (1, '有借有还'),
        (2, '还借欠债'),
    )
    order_status = (
        (0, '已取消'),
        (1, '未递交'),
        (2, '待批准'),
        (3, '待调拨'),
        (4, '已完成'),
        (5, '已取消'),
    )
    allot_order_id = models.CharField(max_length=30, verbose_name='虚拟调拨单号')
    vwarehouse_ori = models.ForeignKey(WarehouseVirtual, related_name='vwareori', on_delete=models.CASCADE, verbose_name='源虚拟仓')
    vwarehouse_des = models.ForeignKey(WarehouseVirtual, related_name='vwaredes', on_delete=models.CASCADE, verbose_name='目的虚拟仓')
    category = models.SmallIntegerField(choices=CATEGORY, default=0, verbose_name='类型')
    goods_name = models.ForeignKey(GoodsInfo, on_delete=models.CASCADE, verbose_name='货品名称')
    quantity = models.IntegerField(verbose_name='调拨数量')
    memorandum = models.CharField(max_length=200, null=True, blank=True, verbose_name='备注')