# -*- coding: utf-8 -*-
# @Time    : 2019/11/17 20:19
# @Author  : Hann
# @Site    :
# @File    : adminx.py
# @Software: PyCharm

from django.db import models
from db.base_model import BaseModel
from apps.base.company.models import ManuInfo


class SeriesInfo(BaseModel):
    ORDER_STATUS = (
        (0, '取消'),
        (1, '正常'),
    )
    s_name = models.CharField(unique=True, max_length=100, verbose_name='系列名称')
    category = models.CharField(null=True, blank=True, max_length=100, verbose_name='系列类型')
    order_status = models.SmallIntegerField(choices=ORDER_STATUS, default=1, verbose_name='系列状态')

    class Meta:
        verbose_name = 'B-产品-系列'
        verbose_name_plural = verbose_name
        db_table = 'base_goods_series'

    def __str__(self):
        return self.s_name

    @classmethod
    def verify_mandatory(cls, columns_key):
        VERIFY_FIELD = ['s_name']

        for i in VERIFY_FIELD:
            if i not in columns_key:
                return 'verify_field error, must have mandatory field: "{}""'.format(i)
        else:
            return None


class BarCodeInfo(BaseModel):
    ORDER_STATUS = (
        (0, '取消'),
        (1, '正常'),
    )
    barcode = models.CharField(max_length=90, verbose_name='条码')
    order_status = models.SmallIntegerField(choices=ORDER_STATUS, default=1, verbose_name='条码状态')

    class Meta:
        verbose_name = 'B-产品-条码'
        verbose_name_plural = verbose_name
        db_table = 'base_goods_barcode'

    def __str__(self):
        return self.barcode


class GoodsInfo(BaseModel):
    ORDER_STATUS = (
        (0, '取消'),
        (1, '正常'),
    )

    goods_name = models.CharField(max_length=150, verbose_name='物料名称')
    goods_id = models.CharField(unique=True, max_length=150, verbose_name='物料编码', db_index=True)
    size = models.CharField(null=True, blank=True, max_length=150, verbose_name='规格')
    manufactory = models.ForeignKey(ManuInfo, on_delete=models.CASCADE, null=True, blank=True, verbose_name='供应商')
    series = models.ForeignKey(SeriesInfo, null=True, blank=True, on_delete=models.CASCADE, verbose_name='系列')
    e_name = models.CharField(max_length=200, null=True, blank=True, verbose_name='英文名')
    p_name = models.CharField(max_length=200, null=True, blank=True, verbose_name='产地名')
    price = models.FloatField(verbose_name='含税单价')
    package_unit = models.IntegerField(null=True, blank=True, verbose_name='装箱规格')
    shelf_life = models.IntegerField(null=True, blank=True, verbose_name='保质期')
    logistics_time = models.IntegerField(null=True, blank=True, verbose_name='物流周期')
    order_time = models.IntegerField(null=True, blank=True, verbose_name='订货周期')
    moq = models.IntegerField(null=True, blank=True, verbose_name='起订量')
    memorandum = models.CharField(max_length=360, null=True, blank=True, verbose_name='备注')
    order_status = models.SmallIntegerField(choices=ORDER_STATUS, default=1, verbose_name='货品状态')

    class Meta:
        verbose_name = 'B-产品-货品'
        verbose_name_plural = verbose_name
        db_table = 'base_goods_goods'

    def __str__(self):
        return '{0}'.format(self.goods_name)

    def order_cycle(self):
        try:
            order_cycle_month = int(self.order_time)/30
        except Exception as e:
            order_cycle_month = 0
        finally:
            order_cycle_month = '%.2f 月' % order_cycle_month
        return order_cycle_month

    order_cycle.short_description = '订货周期（月）'

    @classmethod
    def verify_mandatory(cls, columns_key):
        VERIFY_FIELD = ['series', 'goods_id', 'goods_name', 'size', 'price', 'package_unit', 'shelf_life', 'logistics_time', 'order_time', 'moq']

        for i in VERIFY_FIELD:
            if i not in columns_key:
                return 'verify_field error, must have mandatory field: "{}""'.format(i)
        else:
            return None