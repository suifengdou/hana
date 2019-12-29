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

from apps.wms.stock.models import DeptStockInfo



class VirtualAllot(BaseModel):
    CATEGORY = (
        (0, '有借无还'),
        (1, '有借有还'),
        (2, '还债'),
    )
    ORDER_STATUS = (
        (0, '已取消'),
        (1, '未递交'),
        (2, '待同意'),
        (3, '待执行'),
        (4, '已完成'),
    )
    ERROR_LIST = (
        (0, '正常'),
        (1, '可借存货不足'),
        (2, '可还存货不足'),
    )
    allot_order_id = models.CharField(max_length=30, verbose_name='虚拟调拨单号')
    department = models.ForeignKey(DepartmentInfo, on_delete=models.CASCADE, verbose_name='源部门')
    vwarehouse_ori = models.ForeignKey(DeptStockInfo, related_name='vwareori', on_delete=models.CASCADE, verbose_name='源虚拟仓')
    vwarehouse_des = models.ForeignKey(WarehouseVirtual, related_name='vwaredes', on_delete=models.CASCADE, verbose_name='目的虚拟仓')
    category = models.SmallIntegerField(choices=CATEGORY, default=0, verbose_name='类型')
    goods_name = models.ForeignKey(GoodsInfo, on_delete=models.CASCADE, verbose_name='货品名称')
    goods_id = models.CharField(max_length=60, verbose_name='物料编码', db_index=True)
    quantity = models.IntegerField(verbose_name='调拨数量')
    memorandum = models.CharField(max_length=200, null=True, blank=True, verbose_name='备注')
    order_status = models.SmallIntegerField(choices=ORDER_STATUS, default=1, verbose_name='单据状态')
    error_tag = models.SmallIntegerField(choices=ERROR_LIST, default=0, verbose_name='错误原因')
    checker = models.CharField(max_length=30, null=True, blank=True, verbose_name='审核人')

    class Meta:
        verbose_name = 'oms-a-调拨查询'
        verbose_name_plural = verbose_name
        db_table = 'oms_vwm_allot'


class VAPending(VirtualAllot):

    class Meta:
        verbose_name = 'oms-a-未递交调拨'
        verbose_name_plural = verbose_name
        proxy = True


class VACheck(VirtualAllot):

    class Meta:
        verbose_name = 'oms-a-未同意调拨'
        verbose_name_plural = verbose_name
        proxy = True


class VAProcess(VirtualAllot):

    class Meta:
        verbose_name = 'oms-a-未执行调拨'
        verbose_name_plural = verbose_name
        proxy = True