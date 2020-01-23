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
from apps.oms.purchase.models import PurchaseInfo


class OriStockInInfo(BaseModel):

    ORDER_STATUS = (
        (0, '已取消'),
        (1, '未递交'),
        (2, '已递交'),
    )

    MISTAKE_TAG = (
        (0, '正常'),
        (1, '入库合并'),
        (2, '重复递交'),
        (3, '非法工厂'),
        (4, '非法货品'),
        (5, '非法仓库'),
        (6, '采购单错误'),
    )

    order_category = models.CharField(max_length=60, verbose_name='单据类型')
    order_creator = models.CharField(max_length=60, verbose_name='创建人')
    supplier = models.CharField(max_length=60, verbose_name='供货方')
    create_date = models.DateTimeField(max_length=60, verbose_name='创建日期')
    seller = models.CharField(max_length=60, verbose_name='结算方')
    bs_category = models.CharField(max_length=60, verbose_name='业务类型')
    stockin_order_id = models.CharField(max_length=60, verbose_name='单据编号', db_index=True)
    last_modifier = models.CharField(max_length=60, verbose_name='最后修改人')
    payee = models.CharField(max_length=60, verbose_name='收款方')
    stockin_time = models.DateTimeField(max_length=60, verbose_name='入库日期')
    last_modify_time = models.DateTimeField(max_length=60, verbose_name='最后修改日期')
    purchaser = models.CharField(max_length=60, verbose_name='采购组织')
    demander = models.CharField(max_length=60, verbose_name='需求组织')
    goods_id = models.CharField(max_length=60, verbose_name='物料编码', db_index=True)
    goods_name = models.CharField(max_length=60, verbose_name='物料名称')
    goods_size = models.CharField(max_length=60, verbose_name='规格型号')
    goods_unit = models.CharField(max_length=60, verbose_name='库存单位')
    quantity_receivable = models.IntegerField(default=0, verbose_name='应收数量')
    quantity_received = models.IntegerField(verbose_name='实收数量')
    batch_number = models.CharField(max_length=60, verbose_name='批号', db_index=True)
    warehouse = models.CharField(max_length=60, verbose_name='仓库', db_index=True)
    expiry_date = models.DateTimeField(max_length=60, verbose_name='有效期至')
    produce_time = models.DateTimeField(max_length=60, verbose_name='生产日期')
    memorandum = models.CharField(max_length=60, null=True, blank=True, verbose_name='备注')
    origin_order_category = models.CharField(max_length=60, verbose_name='源单类型')
    origin_order_id = models.CharField(max_length=60, verbose_name='源单编号')
    payable_quantity = models.IntegerField(verbose_name='关联应付数量（计价基本）')
    purchase_order_id = models.CharField(max_length=60, verbose_name='订单单号')
    assist_quantity = models.IntegerField(verbose_name='实收数量(辅单位)')
    multiple = models.IntegerField(verbose_name='主/辅换算率')
    price = models.IntegerField(verbose_name='成本价')
    storage = models.CharField(max_length=60, null=True, blank=True, verbose_name='仓位')

    order_status = models.SmallIntegerField(choices=ORDER_STATUS, default=1, verbose_name='订单状态', db_index=True)
    mistake_tag = models.SmallIntegerField(choices=MISTAKE_TAG, default=0, verbose_name='错误标识')

    class Meta:
        verbose_name = 'wms-原始入库单查询'
        verbose_name_plural = verbose_name
        db_table = 'wms_s_oristockin'

    def __str__(self):
        return str(self.stockin_order_id)


class OriStockInPending(OriStockInInfo):

    class Meta:
        verbose_name = 'wms-原始入库单未递交'
        verbose_name_plural = verbose_name
        proxy =True

    @classmethod
    def verify_mandatory(cls, columns_key):
        VERIFY_FIELD = ['row_number', 'stockin_order_id', 'last_modifier', 'payee',
                        'stockin_time', 'last_modify_time', 'purchaser', 'demander',
                        'goods_id', 'goods_name', 'goods_size', 'goods_unit',
                        'quantity_receivable', 'quantity_received', 'batch_number', 'warehouse', 'expiry_date',
                        'produce_time', 'origin_order_category', 'origin_order_id',
                        'payable_quantity', 'purchase_order_id', 'assist_quantity', 'multiple', ]
        for i in VERIFY_FIELD:
            if i not in columns_key:
                return 'verify_field error, must have mandatory field: "{}""'.format(i)
        else:
            return None


class StockInInfo(BaseModel):
    ORDER_STATUS = (
        (0, '已取消'),
        (1, '未审核'),
        (2, '待核销'),
        (3, '已完成'),
    )

    MISTAKE_TAG = (
        (0, '正常'),
        (1, '原始单缺漏'),
        (2, '入库数量大于采购数量'),
        (3, '保存库存错误'),
        (4, '货品错误'),
        (5, '采购单错误'),
        (5, '采购单数量错误'),
    )

    order_category = models.CharField(max_length=60, verbose_name='单据类型')
    order_creator = models.CharField(max_length=60, verbose_name='创建人')
    supplier = models.ForeignKey(CompanyInfo, on_delete=models.CASCADE, verbose_name='供货方')
    create_date = models.DateTimeField(max_length=60, verbose_name='创建日期')
    seller = models.CharField(max_length=60, verbose_name='结算方')
    bs_category = models.CharField(max_length=60, verbose_name='业务类型')
    stockin_order_id = models.CharField(max_length=60, verbose_name='单据编号', unique=True)
    last_modifier = models.CharField(max_length=60, verbose_name='最后修改人')
    payee = models.CharField(max_length=60, verbose_name='收款方')
    stockin_time = models.DateTimeField(max_length=60, verbose_name='入库日期')
    last_modify_time = models.DateTimeField(max_length=60, verbose_name='最后修改日期')
    purchaser = models.CharField(max_length=60, verbose_name='采购组织')
    demander = models.CharField(max_length=60, verbose_name='需求组织')
    goods_id = models.CharField(max_length=60, verbose_name='物料编码', db_index=True)
    goods_name = models.ForeignKey(GoodsInfo, on_delete=models.CASCADE, verbose_name='物料名称')
    goods_size = models.CharField(max_length=60, verbose_name='规格型号')
    goods_unit = models.CharField(max_length=60, verbose_name='库存单位')
    quantity_receivable = models.IntegerField(null=True, blank=True, verbose_name='应收数量')
    quantity_received = models.IntegerField(verbose_name='实收数量')
    batch_number = models.CharField(max_length=60, verbose_name='批号')
    warehouse = models.ForeignKey(WarehouseInfo, on_delete=models.CASCADE, verbose_name='仓库')
    expiry_date = models.DateTimeField(max_length=60, verbose_name='有效期至')
    produce_time = models.DateTimeField(max_length=60, verbose_name='生产日期')
    memorandum = models.CharField(max_length=60, null=True, blank=True, verbose_name='备注')
    origin_order_category = models.CharField(max_length=60, verbose_name='源单类型')
    origin_order_id = models.CharField(max_length=60, verbose_name='源单编号')
    payable_quantity = models.IntegerField(verbose_name='关联应付数量（计价基本）')
    purchase_order_id = models.ForeignKey(PurchaseInfo, on_delete=models.CASCADE, verbose_name='订单单号')
    assist_quantity = models.IntegerField(verbose_name='实收数量(辅单位)')
    multiple = models.IntegerField(verbose_name='主/辅换算率')

    price = models.IntegerField(verbose_name='成本价')

    quantity_linking = models.IntegerField(default=0, verbose_name='关联存货数量')
    order_status = models.SmallIntegerField(choices=ORDER_STATUS, default=1, verbose_name='订单状态', db_index=True)
    mistake_tag = models.SmallIntegerField(choices=MISTAKE_TAG, default=0, verbose_name='错误标识')

    class Meta:
        verbose_name = 'wms-入库单查询'
        verbose_name_plural = verbose_name
        db_table = 'wms_s_stockin'

    def __str__(self):
        return str(self.stockin_order_id)


class StockInPending(StockInInfo):

    class Meta:
        verbose_name = 'wms-入库单未审核'
        verbose_name_plural = verbose_name
        proxy = True


