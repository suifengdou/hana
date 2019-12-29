# -*- coding: utf-8 -*-
# @Time    : 2019/12/3 8:56
# @Author  : Hann
# @Site    : 
# @File    : adminx.py
# @Software: PyCharm

from django.db import models
import django.utils.timezone as timezone
from django.db.models import Sum, Avg, Min, Max

from db.base_model import BaseModel
from apps.base.department.models import DepartmentInfo
from apps.base.goods.models import GoodsInfo
from apps.base.warehouse.models import WarehouseVirtual
from apps.wms.stock.models import StockInfo


class DistributionInfo(BaseModel):

    ORDER_STATUS = (
        (0, '已取消'),
        (1, '未审核'),
        (2, '已审核'),
    )
    category = (
        (0, '预分配单'),
        (1, '预分配单'),
    )
    ERROR_LIST = (
        (0, '正常'),
        (1, '可用库存不足'),
        (2, '正常'),
        (3, '正常'),
    )

    distribution_order_id = models.CharField(max_length=50, verbose_name='分配单号')
    warehouse = models.ForeignKey(StockInfo, on_delete=models.CASCADE, verbose_name='实仓')
    department = models.ForeignKey(DepartmentInfo, on_delete=models.CASCADE, verbose_name='部门')
    goods_name = models.ForeignKey(GoodsInfo, on_delete=models.CASCADE, verbose_name='货品名称')
    goods_id = models.CharField(max_length=60, verbose_name='物料编码', db_index=True)
    quantity = models.IntegerField(verbose_name='分配数量')
    memorandum = models.CharField(null=True, blank=True, max_length=200, verbose_name='备注')
    vwarehouse = models.ForeignKey(WarehouseVirtual, related_name='vwaredis', on_delete=models.CASCADE, verbose_name='虚拟仓')
    order_status = models.SmallIntegerField(choices=ORDER_STATUS, default=1, verbose_name='单据状态')
    error_tag = models.SmallIntegerField(choices=ERROR_LIST, default=0, verbose_name='错误原因')

    class Meta:
        verbose_name = 'oms-预分配'
        verbose_name_plural = verbose_name
        db_table = 'oms_pdb_distribution'

    def __str__(self):
        return self.distribution_order_id


class Undistribution(DistributionInfo):

    class Meta:
        verbose_name = 'oms-未审核预分配'
        verbose_name_plural = verbose_name
        proxy = True

    def undistribution_q(self):
        undis_quantiy = self.warehouse.undistributed
        if not undis_quantiy:
            undis_quantiy = 0
        return undis_quantiy
    undistribution_q.short_description = '未分配数量'

    def available_q(self):
        occupy_quantity = Undistribution.objects.filter(goods_name=self.goods_name, order_status=1).aggregate(Sum('quantity'))['quantity__sum']
        if occupy_quantity:
            avail_quantity = self.warehouse.undistributed - occupy_quantity
        else:
            avail_quantity = self.warehouse.undistributed
        return avail_quantity
    available_q.short_description = '可用分配数量'

