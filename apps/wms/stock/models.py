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
from apps.base.warehouse.models import WarehouseInfo, WarehouseVirtual
from apps.base.department.models import CentreInfo


class StockInfo(BaseModel):

    ORDER_STATUS = (
        (0, '库存锁定'),
        (1, '等待分配'),
        (2, '分配完成'),
    )

    goods_name = models.ForeignKey(GoodsInfo, on_delete=models.CASCADE, verbose_name='货品名称')
    goods_id = models.CharField(max_length=60, verbose_name='物料编码', db_index=True)
    warehouse = models.ForeignKey(WarehouseInfo, on_delete=models.CASCADE, verbose_name='仓库')
    quantity = models.IntegerField(verbose_name='库存')
    undistributed = models.IntegerField(verbose_name='未分配库存')
    memorandum = models.CharField(null=True, blank=True, max_length=200, verbose_name='备注')

    order_status = models.SmallIntegerField(choices=ORDER_STATUS, default=1, verbose_name='库存状态')

    class Meta:
        verbose_name = 'WMS-库存-实仓'
        verbose_name_plural = verbose_name
        index_together = ['goods_name', 'warehouse']
        db_table = 'wms_stock_stock'

    def __str__(self):
        return str(self.warehouse)


class DeptStockInfo(BaseModel):
    ORDER_STATUS = (
        (0, '库存锁定'),
        (1, '正常销售'),
    )
    centre = models.ForeignKey(CentreInfo, on_delete=models.CASCADE, verbose_name='部门名称')
    goods_name = models.ForeignKey(GoodsInfo, on_delete=models.CASCADE, verbose_name='货品名称')
    goods_id = models.CharField(max_length=60, verbose_name='物料编码', db_index=True)
    warehouse = models.ForeignKey(WarehouseInfo, on_delete=models.CASCADE, verbose_name='仓库')
    vwarehouse = models.ForeignKey(WarehouseVirtual, related_name='vware', on_delete=models.CASCADE, verbose_name='部门仓')
    quantity = models.IntegerField(verbose_name='库存')
    memorandum = models.CharField(null=True, blank=True, max_length=200, verbose_name='备注')

    order_status = models.SmallIntegerField(choices=ORDER_STATUS, default=1, verbose_name='库存状态')

    class Meta:
        verbose_name = 'WMS-库存-部门仓'
        verbose_name_plural = verbose_name
        index_together = ['centre', 'goods_name', 'warehouse', 'vwarehouse']
        db_table = 'wms_stock_deptstock'

    def __str__(self):
        return str(self.vwarehouse)


class MyDeptStock(DeptStockInfo):

    class Meta:
        verbose_name = 'WMS-库存-我的部门'
        verbose_name_plural = verbose_name
        proxy = True


class TransDeptStock(DeptStockInfo):

    class Meta:
        verbose_name = 'WMS-库存-中转仓'
        verbose_name_plural = verbose_name
        proxy = True

