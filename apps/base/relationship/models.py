# -*- coding: utf-8 -*-
# @Time    : 2019/11/19 20:14
# @Author  : Hann
# @Site    :
# @File    : adminx.py
# @Software: PyCharm

from db.base_model import BaseModel
from django.db import models

from apps.base.goods.models import BarCodeInfo, GoodsInfo, SeriesInfo
from apps.base.company.models import ManuInfo
from apps.base.department.models import DepartmentInfo
from apps.base.warehouse.models import WarehouseManu, WarehouseGeneral


class BarCodeToGoods(BaseModel):
    ORDER_STATUS = (
        (0, '取消'),
        (1, '正常'),
    )
    barcode = models.ForeignKey(BarCodeInfo, models.CASCADE, verbose_name='条码')
    goods = models.ForeignKey(GoodsInfo, models.CASCADE, verbose_name='货品')
    order_status = models.SmallIntegerField(choices=ORDER_STATUS, default=1, verbose_name='单据状态')

    class Meta:
        unique_together = ('barcode', 'goods')
        verbose_name = 'B-关联-条码2货品'
        verbose_name_plural = verbose_name
        db_table = 'base_rel_barcode2goods'

    def __str__(self):
        return '{0}to{1}'.format(self.barcode.barcode, self.goods.goods_name)


class DepartmentToWarehouse(BaseModel):
    ORDER_STATUS = (
        (0, '取消'),
        (1, '正常'),
    )
    department = models.ForeignKey(DepartmentInfo, models.CASCADE, verbose_name='部门')
    warehouse = models.ForeignKey(WarehouseGeneral, models.CASCADE, verbose_name='仓库')
    order_status = models.SmallIntegerField(choices=ORDER_STATUS, default=1, verbose_name='单据状态')

    class Meta:
        unique_together = ('department', 'warehouse')
        verbose_name = 'B-关联-部门2仓库'
        verbose_name_plural = verbose_name
        db_table = 'base_rel_dept2ware'


class ManuToWarehouse(BaseModel):
    ORDER_STATUS = (
        (0, '取消'),
        (1, '正常'),
    )
    manufactory = models.ForeignKey(ManuInfo, models.CASCADE, verbose_name='工厂')
    warehouse = models.ForeignKey(WarehouseManu, models.CASCADE, verbose_name='仓库')
    order_status = models.SmallIntegerField(choices=ORDER_STATUS, default=1, verbose_name='单据状态')

    class Meta:
        unique_together = ('manufactory', 'warehouse')
        verbose_name = 'B-关联-工厂2仓库'
        verbose_name_plural = verbose_name
        db_table = 'base_rel_manu2ware'