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
from apps.base.company.models import MineInfo, ManuInfo
from apps.base.goods.models import GoodsInfo


class PurchaseInfo(BaseModel):

    ORDER_STATUS = (
        (0, '已取消'),
        (1, '待生产'),
        (2, '在生产'),
        (3, '已完成'),
    )

    purchase_order_id = models.CharField(max_length=50, verbose_name='单据编号')
    purchase_time = models.DateTimeField(max_length=50, verbose_name='采购时间')
    supplier = models.ForeignKey(ManuInfo, on_delete=models.CASCADE, verbose_name='供应商')
    status = models.CharField(max_length=50, verbose_name='单据状态')
    puchaser = models.CharField(max_length=50, verbose_name='采购组织')
    is_cancel = models.CharField(max_length=50, verbose_name='关闭状态')
    goods_unit = models.CharField(max_length=50, verbose_name='采购单位')
    quantity = models.IntegerField(verbose_name='采购数量')
    delivery_date = models.DateTimeField(verbose_name='交货日期')
    price = models.FloatField(verbose_name='含税单价')
    goods_id = models.CharField(max_length=60, verbose_name='物料编码', db_index=True)
    goods_name = models.ForeignKey(GoodsInfo, on_delete=models.CASCADE, verbose_name='物料名称')
    is_gift = models.CharField(max_length=50, verbose_name='是否赠品')
    is_close = models.CharField(max_length=50, verbose_name='业务关闭')

    complete_quantity = models.IntegerField(default=0, verbose_name='采购完成数量')
    order_status = models.SmallIntegerField(choices=ORDER_STATUS, default=1, verbose_name='订单状态')

    class Meta:
        verbose_name = 'oms-采购单查询'
        verbose_name_plural = verbose_name
        unique_together = ('purchase_order_id', 'goods_id')
        db_table = 'oms_purchase_order'

    def __str__(self):
        return str(self.purchase_order_id)


class PurchasePending(PurchaseInfo):

    class Meta:
        verbose_name = 'oms-采购单一览'
        verbose_name_plural = verbose_name
        proxy = True