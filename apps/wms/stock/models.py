# -*- coding: utf-8 -*-
# @Time    : 2019/12/2 21:35
# @Author  : Hann
# @Site    : 
# @File    : adminx.py
# @Software: PyCharm

from django.db import models
import django.utils.timezone as timezone

from db.base_model import BaseModel
from apps.base.goods.models import GoodsInfo
from apps.base.warehouse.models import WarehouseGeneral, WarehouseVirtual


class StockInfo(BaseModel):

    ORDER_STATUS = (
        (0, '库存锁定'),
        (1, '等待分配'),
        (2, '分配完成'),
    )

    goods_name = models.ForeignKey(GoodsInfo, on_delete=models.CASCADE, verbose_name='货品名称')
    goods_id = models.CharField(max_length=60, verbose_name='物料编码')
    warehouse = models.ForeignKey(WarehouseGeneral, on_delete=models.CASCADE, verbose_name='仓库')
    quantity = models.IntegerField(verbose_name='库存')
    undistributed = models.IntegerField(verbose_name='未分配库存')
    memorandum = models.CharField(null=True, blank=True, max_length=200, verbose_name='备注')

    order_status = models.SmallIntegerField(choices=ORDER_STATUS, default=1, verbose_name='库存状态')

    class Meta:
        verbose_name = 'WMS-库存-实仓'
        verbose_name_plural = verbose_name
        db_table = 'wms_stock_stock'


class DeptStockInfo(BaseModel):
    ORDER_STATUS = (
        (0, '库存锁定'),
        (1, '正常销售'),
    )
    goods_name = models.ForeignKey(GoodsInfo, on_delete=models.CASCADE, verbose_name='货品名称')
    goods_id = models.CharField(max_length=60, verbose_name='物料编码')
    warehouse = models.ForeignKey(WarehouseGeneral, on_delete=models.CASCADE, verbose_name='仓库')
    vwarehouse = models.ForeignKey(WarehouseVirtual, related_name='vware', on_delete=models.CASCADE, verbose_name='虚拟仓')
    quantity = models.IntegerField(verbose_name='库存')
    memorandum = models.CharField(null=True, blank=True, max_length=200, verbose_name='备注')

    order_status = models.SmallIntegerField(choices=ORDER_STATUS, default=1, verbose_name='库存状态')

    class Meta:
        verbose_name = 'WMS-库存-部门仓'
        verbose_name_plural = verbose_name
        db_table = 'wms_stock_deptstock'


