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
from apps.base.company.models import CompanyInfo
from apps.base.warehouse.models import WarehouseInfo
from apps.base.goods.models import GoodsInfo
from apps .base.department.models import DepartmentInfo


class CovertSI(BaseModel):
    ORDER_STATUS = (
        (0, '已取消'),
        (1, '未审核'),
        (2, '已完成'),
    )

    MISTAKE_TAG = (
        (0, '正常'),
        (1, '未设置部门仓库'),
        (2, '多线程重复操作'),
        (3, '实仓实例保存错误'),
        (4, '部门仓实例保存错误'),

    )
    CATEGORY = (
        (0, '独立入库'),
        (1, '全局入库'),
    )
    order_id = models.CharField(max_length=60, verbose_name='单据编号', unique=True, db_index=True)
    order_category = models.SmallIntegerField(choices=CATEGORY, default=0, verbose_name='单据类型')
    supplier = models.ForeignKey(CompanyInfo, on_delete=models.CASCADE, verbose_name='供货方')
    department = models.ForeignKey(DepartmentInfo, on_delete=models.CASCADE, verbose_name='部门')
    create_date = models.DateTimeField(verbose_name='创建日期')
    seller = models.CharField(max_length=60, verbose_name='结算方')

    ori_creator = models.CharField(max_length=60, null=True, blank=True, verbose_name='创建人')
    payee = models.CharField(max_length=60, verbose_name='收款方')
    stockin_date = models.DateTimeField(max_length=60, verbose_name='入库日期')
    purchaser = models.CharField(max_length=60, verbose_name='采购组织')
    goods_id = models.CharField(max_length=60, verbose_name='物料编码', db_index=True)
    goods_name = models.ForeignKey(GoodsInfo, on_delete=models.CASCADE, verbose_name='物料名称')
    quantity_receivable = models.IntegerField(null=True, blank=True, verbose_name='应收数量')
    quantity_received = models.IntegerField(verbose_name='实收数量')
    batch_number = models.CharField(null=True, blank=True, max_length=60, verbose_name='批号')
    warehouse = models.ForeignKey(WarehouseInfo, on_delete=models.CASCADE, verbose_name='仓库')
    expiry_date = models.DateTimeField(max_length=60, verbose_name='有效期至')
    produce_date = models.DateTimeField(max_length=60, verbose_name='生产日期')
    memorandum = models.CharField(max_length=300, null=True, blank=True, verbose_name='备注')
    origin_order_category = models.CharField(max_length=60, verbose_name='源单类型')
    origin_order_id = models.CharField(max_length=60, verbose_name='源单编号')
    price = models.IntegerField(verbose_name='单价')

    quantity_linking = models.IntegerField(default=0, verbose_name='关联存货数量')
    order_status = models.SmallIntegerField(choices=ORDER_STATUS, default=1, verbose_name='订单状态', db_index=True)
    mistake_tag = models.SmallIntegerField(choices=MISTAKE_TAG, default=0, verbose_name='错误标识')

    class Meta:
        verbose_name = 'oms-入库调整单查询'
        verbose_name_plural = verbose_name
        db_table = 'oms_convert_stockin'

    def __str__(self):
        return str(self.order_id)


class CovertSIUnhandle(CovertSI):

    class Meta:
        verbose_name = 'oms-入库调整单未审核'
        verbose_name_plural = verbose_name
        proxy = True

    def __str__(self):
        return str(self.order_id)


class CovertSO(BaseModel):
    ORDER_STATUS = (
        (0, '已取消'),
        (1, '待递交'),
        (2, '已完成'),
    )
    ERROR_LIST = (
        (0, '正常'),
        (1, '多线程重复操作'),
        (2, '部门存货不足'),
        (3, '保存历史记录失败'),
        (4, '保存部门仓失败'),
        (5, '保存实仓失败'),
        (6, '保存部门仓失败'),
        (7, '部门没有此货品'),
    )
    CATEGORY = (
        (0, '独立出库'),
        (1, '全局出库'),
    )

    order_id = models.CharField(max_length=30, verbose_name='单据编号')
    customer = models.CharField(max_length=60, verbose_name='客户')
    order_category = models.SmallIntegerField(choices=CATEGORY, default=0, verbose_name='单据类型')
    origin_order_category = models.CharField(max_length=20, verbose_name='源单类型')
    origin_order_id = models.CharField(max_length=60, verbose_name='源单编号')
    sale_organization = models.CharField(max_length=30, verbose_name='销售组织')
    department = models.ForeignKey(DepartmentInfo, on_delete=models.CASCADE, verbose_name='部门')
    memorandum = models.CharField(null=True, blank=True, max_length=300, verbose_name='备注')
    ori_creator = models.CharField(max_length=30, verbose_name='创建人')
    date = models.DateTimeField(verbose_name='日期')
    goods_id = models.CharField(max_length=50, verbose_name='物料编码')
    goods_name = models.ForeignKey(GoodsInfo, on_delete=models.CASCADE, verbose_name='物料名称')
    quantity = models.IntegerField(verbose_name='实发数量')
    warehouse = models.ForeignKey(WarehouseInfo, on_delete=models.CASCADE, verbose_name='仓库')
    price = models.FloatField(verbose_name='含税单价')
    amount = models.FloatField(verbose_name='价税合计')
    buyer = models.CharField(max_length=60, null=True, blank=True, verbose_name='收货方')
    address = models.CharField(max_length=240, null=True, blank=True, verbose_name='收货方地址')

    mistake_tag = models.SmallIntegerField(choices=ERROR_LIST, default=0, verbose_name='错误原因')
    order_status = models.SmallIntegerField(choices=ORDER_STATUS, default=1, verbose_name='状态')

    class Meta:
        verbose_name = 'oms-出库调整单查询'
        verbose_name_plural = verbose_name
        db_table = 'oms_convert_stockout'

    def __str__(self):
        return str(self.order_id)


class CovertSOUnhandle(CovertSO):

    class Meta:
        verbose_name = 'oms-出库调整单未审核'
        verbose_name_plural = verbose_name
        proxy = True

    def __str__(self):
        return str(self.order_id)


class StockoutList(BaseModel):
    ORDER_STATUS = (
        (0, '已取消'),
        (1, '已完成'),
    )
    order_id = models.CharField(max_length=30, verbose_name='出库调整单单号', unnique=True, db_index=True)
    si_order_id = models.CharField(max_length=300, verbose_name='入库调整单单号', null=True, blank=True)

    order_status = models.SmallIntegerField(choices=ORDER_STATUS, default=1, verbose_name='状态')

    class Meta:
        verbose_name = 'oms-出库调整单已出库列表'
        verbose_name_plural = verbose_name
        db_table = 'oms_convert_solist'