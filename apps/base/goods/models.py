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


class SizeInfo(BaseModel):
    ORDER_STATUS = (
        (0, '取消'),
        (1, '正常'),
    )
    s_name = models.CharField(unique=True, max_length=50, verbose_name='规格名称')
    unit = models.CharField(max_length=50, verbose_name='度量单位')
    value = models.IntegerField(verbose_name='数值')
    multiple = models.IntegerField(verbose_name='最小包装数量')
    multiple_unit = models.CharField(max_length=50, null=True, blank=True, verbose_name='倍数单位')
    memorandum = models.CharField(null=True, blank=True, max_length=100, verbose_name='备注')
    order_status = models.SmallIntegerField(choices=ORDER_STATUS, default=1, verbose_name='规格状态')

    class Meta:
        verbose_name = 'B-产品-规格'
        verbose_name_plural = verbose_name
        db_table = 'base_goods_size'

    def __str__(self):
        return self.s_name


class OPackagesInfo(BaseModel):
    ORDER_STATUS = (
        (0, '取消'),
        (1, '正常'),
    )
    p_name = models.CharField(unique=True, max_length=50, verbose_name='装箱外箱名称')
    length = models.IntegerField(verbose_name='长')
    width = models.IntegerField(verbose_name='宽')
    height = models.IntegerField(verbose_name='高')
    order_status = models.SmallIntegerField(choices=ORDER_STATUS, default=1, verbose_name='外箱状态')

    class Meta:
        verbose_name = 'B-产品-装箱外箱'
        verbose_name_plural = verbose_name
        db_table = 'base_goods_opackage'

    def __str__(self):
        return '{0}*{1}*{2}'.format(self.length, self.width, self.height)


class IPackagesInfo(BaseModel):
    ORDER_STATUS = (
        (0, '取消'),
        (1, '正常'),
    )
    p_name = models.CharField(unique=True, max_length=50, verbose_name='装箱内箱名称')
    length = models.IntegerField(verbose_name='长')
    width = models.IntegerField(verbose_name='宽')
    height = models.IntegerField(verbose_name='高')
    multiple = models.SmallIntegerField(verbose_name='包装倍数')
    order_status = models.SmallIntegerField(choices=ORDER_STATUS, default=1, verbose_name='内箱状态')

    class Meta:
        verbose_name = 'B-产品-装箱内箱'
        verbose_name_plural = verbose_name
        db_table = 'base_goods_ipackage'

    def __str__(self):
        return '{0}*{1}*{2}'.format(self.length, self.width, self.height)


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
    CATEGORY = (
        (0, '膜'),
        (1, '水'),
        (2, '液'),
        (3, '霜'),
        (4, '膏'),
        (5, '粉'),
    )
    goods_name = models.CharField(max_length=150, verbose_name='货品名称')
    goods_id = models.CharField(unique=True, max_length=150, verbose_name='货品代码')
    size = models.ForeignKey(SizeInfo, on_delete=models.CASCADE, verbose_name='规格')
    manufactory = models.ForeignKey(ManuInfo, on_delete=models.CASCADE, verbose_name='工厂')
    series = models.ForeignKey(SeriesInfo, null=True, blank=True, on_delete=models.CASCADE, verbose_name='系列')
    category = models.SmallIntegerField(choices=CATEGORY, default=0, verbose_name='类型')
    e_name = models.CharField(max_length=200, verbose_name='英文名')
    p_name = models.CharField(max_length=200, verbose_name='产地名')
    price = models.IntegerField(verbose_name='单价')
    logistics_time = models.IntegerField(verbose_name='物流周期（天）')
    order_time = models.IntegerField(verbose_name='订货周期（天）')
    memorandum = models.CharField(max_length=360, null=True, blank=True, verbose_name='备注')
    order_status = models.SmallIntegerField(choices=ORDER_STATUS, default=1, verbose_name='货品状态')
    package_unit = models.IntegerField(null=True, blank=True, verbose_name='装箱规格')

    class Meta:
        unique_together = ('goods_name', 'size')
        verbose_name = 'B-产品-货品'
        verbose_name_plural = verbose_name
        db_table = 'base_goods_goods'

    def __str__(self):
        return '{0}{1}'.format(self.goods_name, self.size)