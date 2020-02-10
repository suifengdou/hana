# -*- coding:  utf-8 -*-
# @Time    :  2019/5/11 13: 47
# @Author  :  Hann
# @Site    :
# @File    :  models.py
# @Software:  PyCharm

from django.db import models
import django.utils.timezone as timezone
import pandas as pd

from db.base_model import BaseModel
from apps.base.department.models import DepartmentInfo
from apps.base.warehouse.models import WarehouseInfo
from apps.base.goods.models import GoodsInfo


class OriStockOut(BaseModel):
    ORDER_STATUS = (
        (0, '已取消'),
        (1, '待递交'),
        (2, '已完成'),
    )
    ERROR_LIST = (
        (0, '正常'),
        (1, '重复递交'),
        (2, '仓库非法'),
        (3, '部门非法'),
        (4, '货品非法'),
    )

    detail_num = models.CharField(max_length=20, verbose_name='明细信息行号')
    date = models.DateTimeField(verbose_name='日期')
    order_id = models.CharField(max_length=30, verbose_name='单据编号')
    customer = models.CharField(max_length=60, verbose_name='客户')
    ori_order_status = models.CharField(max_length=20, verbose_name='单据状态')
    ori_order_category = models.CharField(max_length=20, verbose_name='单据类型')
    sale_organization = models.CharField(max_length=30, verbose_name='销售组织')
    department = models.CharField(max_length=30, verbose_name='销售部门')
    memorandum = models.CharField(max_length=300, verbose_name='备注')
    ori_creator = models.CharField(max_length=30, verbose_name='创建人')
    ori_create_time = models.DateTimeField(verbose_name='创建日期')
    ori_update_time = models.DateTimeField(verbose_name='最后修改日期')
    goods_id = models.CharField(max_length=50, verbose_name='物料编码')
    goods_name = models.CharField(max_length=60, verbose_name='物料名称')
    goods_size = models.CharField(max_length=50, verbose_name='规格型号')
    quantity = models.IntegerField(verbose_name='实发数量')
    warehouse = models.CharField(max_length=50, verbose_name='仓库')
    price = models.CharField(max_length=20, verbose_name='含税单价')
    amount = models.CharField(max_length=30, verbose_name='价税合计')
    package_size = models.IntegerField(verbose_name='主辅换算率')

    error_tag = models.SmallIntegerField(choices=ERROR_LIST, default=0, verbose_name='递交错误原因')
    order_status = models.SmallIntegerField(choices=ORDER_STATUS, default=1, verbose_name='状态')

    class Meta:
        verbose_name = 'wms-原始出库单查询'
        verbose_name_plural = verbose_name
        db_table = 'wms_s_oristockout'
        unique_together = ('detail_num', 'order_id')


class OriStockOutUnhandle(OriStockOut):

    class Meta:
        verbose_name = 'wms-原始出库单处理'
        verbose_name_plural = verbose_name
        proxy = True


class StockOut(BaseModel):
    SOURCE = (
        (0, '销售出库单'),
        (1, '盘亏单'),
        (2, '直接调拨单'),
        (3, '其他出库单'),
        (4, '销售退货单'),
    )
    ORDER_STATUS = (
        (0, '已取消'),
        (1, '待递交'),
        (2, '已完成'),
    )
    ERROR_LIST = (
        (0, '正常'),
        (1, '重复递交'),
        (2, '仓库非法'),
        (3, '部门非法'),
        (4, '货品非法'),
        (5, '库存不足'),
    )
    date = models.DateTimeField(verbose_name='日期')
    order_id = models.CharField(unique=True, max_length=30, verbose_name='单据编号')
    customer = models.CharField(max_length=60, verbose_name='客户')
    ori_order_category = models.CharField(max_length=20, verbose_name='单据类型')
    department = models.ForeignKey(DepartmentInfo, on_delete=models.CASCADE, verbose_name='销售部门')
    memorandum = models.CharField(max_length=300, verbose_name='备注')
    ori_creator = models.CharField(max_length=30, verbose_name='创建人')
    ori_create_time = models.DateTimeField(verbose_name='创建日期')
    ori_update_time = models.DateTimeField(verbose_name='最后修改日期')
    goods_id = models.CharField(max_length=50, verbose_name='物料编码')
    goods_name = models.ForeignKey(GoodsInfo, on_delete=models.CASCADE, verbose_name='物料名称')
    goods_size = models.CharField(max_length=50, verbose_name='规格型号')
    quantity = models.IntegerField(verbose_name='实发数量')
    warehouse = models.ForeignKey(WarehouseInfo, on_delete=models.CASCADE, verbose_name='仓库')
    price = models.IntegerField(max_length=20, verbose_name='含税单价')
    amount = models.FloatField(max_length=30, verbose_name='价税合计')
    package_size = models.IntegerField(verbose_name='主辅换算率')

    source = models.SmallIntegerField(choices=SOURCE, default=0, verbose_name='来源')
    error_tag = models.SmallIntegerField(choices=ERROR_LIST, default=0, verbose_name='递交错误原因')
    order_status = models.SmallIntegerField(choices=ORDER_STATUS, default=1, verbose_name='状态')

    class Meta:
        verbose_name = 'wms-出库单查询'
        verbose_name_plural = verbose_name
        db_table = 'wms_s_oristockout'
        unique_together = ('detail_num', 'order_id')



class StockOutUnhandle(StockOut):
    class Meta:
        verbose_name = 'wms-出库单审理'