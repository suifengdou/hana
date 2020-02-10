# -*- coding: utf-8 -*-
# @Time    : 2020/1/29 8:56
# @Author  : Hann
# @Site    :
# @File    : adminx.py
# @Software: PyCharm

from django.db import models
import django.utils.timezone as timezone

from db.base_model import BaseModel


# 原始采购入库单
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

    detail_num = models.CharField(max_length=20, verbose_name='明细信息行号')
    order_category = models.CharField(max_length=60, verbose_name='单据类型')
    order_creator = models.CharField(max_length=60, verbose_name='创建人')
    supplier = models.CharField(max_length=60, verbose_name='供货方')
    create_date = models.DateTimeField(max_length=60, verbose_name='创建日期')
    seller = models.CharField(max_length=60, verbose_name='结算方')
    bs_category = models.CharField(max_length=60, verbose_name='业务类型')
    order_id = models.CharField(max_length=60, verbose_name='单据编号', db_index=True)
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
    memorandum = models.CharField(null=True, blank=True, max_length=200, verbose_name='备注')
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
        db_table = 'oms_ic_oristockin'

    def __str__(self):
        return "%s-%s" % (str(self.order_id), str(self.detail_num))


class OriStockInUnhandle(OriStockInInfo):

    class Meta:
        verbose_name = 'wms-原始入库单未递交'
        verbose_name_plural = verbose_name
        proxy =True

    @classmethod
    def verify_mandatory(cls, columns_key):
        VERIFY_FIELD = ['detail_num', 'stockin_order_id', 'last_modifier', 'payee',
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


# 原始销售出库单
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
    order_id = models.CharField(max_length=30, verbose_name='单据编号')
    customer = models.CharField(max_length=60, verbose_name='客户')
    ori_order_status = models.CharField(max_length=20, verbose_name='单据状态')
    ori_order_category = models.CharField(max_length=20, verbose_name='单据类型')
    sale_organization = models.CharField(max_length=30, verbose_name='销售组织')
    department = models.CharField(max_length=30, verbose_name='销售部门')
    memorandum = models.CharField(null=True, blank=True, max_length=200, verbose_name='备注')
    ori_creator = models.CharField(max_length=30, verbose_name='创建人')
    date = models.DateTimeField(verbose_name='日期')
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
        db_table = 'oms_ic_oristockout'
        unique_together = ('detail_num', 'order_id')

    def __str__(self):
        return "%s-%s" % (str(self.order_id), str(self.detail_num))


class OriStockOutUnhandle(OriStockOut):
    VERIFY_FIELD = ['detail_num', 'order_id', 'customer', 'ori_order_status', 'ori_order_category', 'sale_organization',
                    'department', 'creator', 'create_date', 'goods_id', 'goods_name', 'goods_size', 'quantity',
                    'warehouse', 'price', 'amount', 'package_size']

    class Meta:
        verbose_name = 'wms-原始出库单处理'
        verbose_name_plural = verbose_name
        proxy = True


    @classmethod
    def verify_mandatory(cls, columns_key):
        for i in cls.VERIFY_FIELD:
            if i not in columns_key:
                return 'verify_field error, must have mandatory field: "{}""'.format(i)
        else:
            return None


# 原始采购单
class OriPurchaseInfo(BaseModel):

    ORDER_STATUS = (
        (0, '已取消'),
        (1, '未递交'),
        (2, '已递交'),
    )
    MISTAKE_TAG = (
        (0, '正常'),
        (1, '货数被并'),
        (2, '导入重复'),
        (3, '工厂非法'),
        (4, '货品非法'),
        (5, '其他错误'),
    )

    detail_num = models.CharField(max_length=20, verbose_name='明细信息行号')
    order_id = models.CharField(max_length=50, verbose_name='单据编号')
    purchase_time = models.DateTimeField(max_length=50, verbose_name='采购时间')
    supplier = models.CharField(max_length=70, verbose_name='供应商')
    status = models.CharField(max_length=50, verbose_name='单据状态')
    puchaser = models.CharField(max_length=60, verbose_name='采购组织')
    is_cancel = models.CharField(max_length=50, verbose_name='关闭状态')
    goods_unit = models.CharField(max_length=50, verbose_name='采购单位')
    quantity = models.IntegerField(verbose_name='采购数量')
    delivery_date = models.DateTimeField(verbose_name='交货日期')
    price = models.FloatField(verbose_name='含税单价')
    goods_id = models.CharField(max_length=60, verbose_name='物料编码', db_index=True)
    goods_name = models.CharField(max_length=60, verbose_name='物料名称')
    is_gift = models.CharField(max_length=50, verbose_name='是否赠品')
    is_close = models.CharField(max_length=50, verbose_name='业务关闭')

    order_status = models.SmallIntegerField(choices=ORDER_STATUS, default=1, verbose_name='状态')
    mistake_tag = models.SmallIntegerField(choices=MISTAKE_TAG, default=0, verbose_name='问题原因')

    class Meta:
        verbose_name = 'oms-原始采购单'
        verbose_name_plural = verbose_name
        unique_together = ('detail_num', 'order_id')
        db_table = 'oms_ic_oripurchase'

    def __str__(self):
        return str(self.order_id)


class OriPurchaseUnhandle(OriPurchaseInfo):
    VERIFY_FIELD = ['order_id', 'purchase_time', 'supplier', 'status', 'puchaser', 'is_cancel', 'goods_unit',
                    'quantity', 'delivery_date', 'goods_id', 'goods_name', 'is_gift', 'is_close']

    class Meta:
        verbose_name = 'oms-未审核原始采购单'
        verbose_name_plural = verbose_name
        proxy = True


    @classmethod
    def verify_mandatory(cls, columns_key):
        for i in cls.VERIFY_FIELD:
            if i not in columns_key:
                return 'verify_field error, must have mandatory field: "{}""'.format(i)
        else:
            return None


# 原始其他出库单
class OriNSStockout(BaseModel):

    ORDER_STATUS = (
        (0, '已取消'),
        (1, '未递交'),
        (2, '已递交'),
    )
    MISTAKE_TAG = (
        (0, '正常'),
        (1, '货数被并'),
        (2, '导入重复'),
        (3, '工厂非法'),
        (4, '货品非法'),
        (5, '其他错误'),
    )

    detail_num = models.CharField(max_length=20, verbose_name='明细信息行号')
    category = models.CharField(max_length=30, verbose_name='单据类型')
    customer = models.CharField(max_length=50, verbose_name='客户')
    department = models.CharField(max_length=50, verbose_name='领料部门')
    owner = models.CharField(max_length=50, verbose_name='货主')
    memorandum = models.CharField(null=True, blank=True, max_length=200, verbose_name='备注')
    order_id = models.CharField(unique=True, max_length=60, verbose_name='单据编号')
    ori_creator = models.CharField(max_length=30, verbose_name='创建人')
    date = models.DateTimeField(max_length='日期')
    goods_id = models.CharField(max_length=60, verbose_name='物料编码', db_index=True)
    goods_name = models.CharField(max_length=60, verbose_name='物料名称')
    goods_size = models.CharField(max_length=30, verbose_name='规格型号')
    quantity = models.IntegerField(verbose_name='实发数量')
    warehouse = models.CharField(max_length=50, verbose_name='发货仓库')
    store_id = models.CharField(max_length=30, verbose_name='店号')
    buyer = models.CharField(max_length=30, verbose_name='收货人')
    smartphone = models.CharField(max_length=30, verbose_name='联系电话')
    address = models.CharField(max_length=200, verbose_name='收货地址')
    out_category = models.CharField(max_length=30, verbose_name='出库类型')

    order_status = models.SmallIntegerField(choices=ORDER_STATUS, default=1, verbose_name='状态')
    mistake_tag = models.SmallIntegerField(choices=MISTAKE_TAG, default=0, verbose_name='问题原因')

    class Meta:
        verbose_name = 'oms-原始其他出库单'
        verbose_name_plural = verbose_name
        unique_together = ('detail_num', 'order_id')
        db_table = 'oms_ic_orinonsalestockout'


class OriNSSOUnhandle(OriNSStockout):
    VERIFY_FIELD = ['detail_num', 'category', 'customer', 'department', 'owner', 'order_id', 'date', 'ori_creator',
                    'create_date', 'goods_id', 'goods_name', 'goods_size', 'quantity', 'warehosue', 'out_category']

    class Meta:
        verbose_name = 'oms-原始未递交其他出库单'
        verbose_name_plural = verbose_name
        proxy = True


    @classmethod
    def verify_mandatory(cls, columns_key):
        for i in cls.VERIFY_FIELD:
            if i not in columns_key:
                return 'verify_field error, must have mandatory field: "{}""'.format(i)
        else:
            return None


# 原始其他入库单
class OriNPStockIn(BaseModel):

    ORDER_STATUS = (
        (0, '已取消'),
        (1, '未递交'),
        (2, '已递交'),
    )
    MISTAKE_TAG = (
        (0, '正常'),
        (1, '货数被并'),
        (2, '导入重复'),
        (3, '工厂非法'),
        (4, '货品非法'),
        (5, '其他错误'),
    )

    detail_num = models.CharField(max_length=20, verbose_name='明细信息行号', db_index=True)
    order_id = models.CharField(max_length=60, verbose_name='单据编号', db_index=True)
    category = models.CharField(max_length=60, verbose_name='单据类型')
    ori_creator = models.CharField(max_length=60, verbose_name='创建人')
    department = models.CharField(max_length=30, verbose_name='部门')
    owner = models.CharField(max_length=50, verbose_name='货主')
    date = models.DateTimeField(max_length=60, verbose_name='日期')

    goods_id = models.CharField(max_length=60, verbose_name='物料编码', db_index=True)
    goods_name = models.CharField(max_length=60, verbose_name='物料名称')
    goods_size = models.CharField(max_length=60, verbose_name='规格型号')
    quantity = models.IntegerField(verbose_name='实收数量')
    batch_number = models.CharField(max_length=60, verbose_name='批号')
    warehouse = models.CharField(max_length=60, verbose_name='仓库', db_index=True)
    expiry_date = models.DateTimeField(max_length=60, verbose_name='有效期至')
    produce_time = models.DateTimeField(max_length=60, verbose_name='生产日期')
    memorandum = models.CharField(null=True, blank=True, max_length=200, verbose_name='备注')
    in_category = models.CharField(max_length=30, verbose_name='入库类型')

    order_status = models.SmallIntegerField(choices=ORDER_STATUS, default=1, verbose_name='状态')
    mistake_tag = models.SmallIntegerField(choices=MISTAKE_TAG, default=0, verbose_name='问题原因')

    class Meta:
        verbose_name = 'oms-原始其他入库单'
        verbose_name_plural = verbose_name
        unique_together = ('detail_num', 'order_id')
        db_table = 'oms_ic_orinonpurstockin'

    def __str__(self):
        return str(self.order_id)


class OriNPSIUnhandle(OriNPStockIn):
    VERIFY_FIELD = ['detail_num', 'order_id', 'category', 'date', 'department', 'ori_creator', 'owner', 'memorandum',
                    'goods_id', 'goods_name', 'goods_size', 'quantity', 'warehouse', 'batch_number', 'produce_time',
                    'expiry_date', 'in_category']

    class Meta:
        verbose_name = 'oms-原始未递交其他入库单'
        verbose_name_plural = verbose_name
        proxy = True


    @classmethod
    def verify_mandatory(cls, columns_key):
        for i in cls.VERIFY_FIELD:
            if i not in columns_key:
                return 'verify_field error, must have mandatory field: "{}""'.format(i)
        else:
            return None


# 原始销售退货单
class OriRefund(BaseModel):

    ORDER_STATUS = (
        (0, '已取消'),
        (1, '未递交'),
        (2, '已递交'),
    )
    MISTAKE_TAG = (
        (0, '正常'),
        (1, '货数被并'),
        (2, '导入重复'),
        (3, '工厂非法'),
        (4, '货品非法'),
        (5, '其他错误'),
    )

    detail_num = models.CharField(max_length=20, verbose_name='明细信息行号', db_index=True)
    order_id = models.CharField(max_length=60, verbose_name='单据编号', db_index=True)
    category = models.CharField(max_length=60, verbose_name='单据类型')
    ori_creator = models.CharField(max_length=60, verbose_name='创建人')
    department = models.CharField(max_length=30, verbose_name='销售部门')
    owner = models.CharField(max_length=50, verbose_name='货主')
    date = models.DateTimeField(max_length=60, verbose_name='日期')
    customer = models.CharField(max_length=60, verbose_name='退货客户')
    memorandum = models.CharField(null=True, blank=True, max_length=200, verbose_name='备注')
    buyer = models.CharField(max_length=50, verbose_name='收货方')
    goods_id = models.CharField(max_length=60, verbose_name='物料编码', db_index=True)
    goods_name = models.CharField(max_length=60, verbose_name='物料名称')
    goods_size = models.CharField(max_length=60, verbose_name='规格型号')
    quantity = models.IntegerField(verbose_name='实退数量')
    refund_date = models.DateTimeField(max_length=60, verbose_name='退货日期')
    batch_number = models.CharField(max_length=60, verbose_name='批号')
    warehouse = models.CharField(max_length=60, verbose_name='仓库', db_index=True)
    expiry_date = models.DateTimeField(max_length=60, verbose_name='有效期至')
    produce_time = models.DateTimeField(max_length=60, verbose_name='生产日期')
    price = models.FloatField(verbose_name='含税单价')
    refund_information = models.CharField(max_length=150, verbose_name='退货单号')
    amount = models.FloatField(verbose_name='价税合计')

    order_status = models.SmallIntegerField(choices=ORDER_STATUS, default=1, verbose_name='状态')
    mistake_tag = models.SmallIntegerField(choices=MISTAKE_TAG, default=0, verbose_name='问题原因')

    class Meta:
        verbose_name = 'oms-原始销售退货单'
        verbose_name_plural = verbose_name
        unique_together = ('detail_num', 'order_id')
        db_table = 'oms_ic_orirefund'

    def __str__(self):
        return str(self.order_id)


class OriRefundUnhandle(OriRefund):
    VERIFY_FIELD = ['detail_num', 'category', 'date', 'order_id', 'customer', 'buyer', 'ori_creator', 'goods_id',
                    'goods_name', 'goods_size', 'quantity', 'refund_date', 'warehouse', 'batch_num', 'produce_date',
                    'expiry_date', 'price', 'amount', 'owner']

    class Meta:
        verbose_name = 'oms-原始未递交销售退货单'
        verbose_name_plural = verbose_name
        proxy = True


    @classmethod
    def verify_mandatory(cls, columns_key):
        for i in cls.VERIFY_FIELD:
            if i not in columns_key:
                return 'verify_field error, must have mandatory field: "{}""'.format(i)
        else:
            return None


# 原始采购退料单
class OriPurRefund(BaseModel):
    ORDER_STATUS = (
        (0, '已取消'),
        (1, '未递交'),
        (2, '已递交'),
    )
    MISTAKE_TAG = (
        (0, '正常'),
        (1, '货数被并'),
        (2, '导入重复'),
        (3, '工厂非法'),
        (4, '货品非法'),
        (5, '其他错误'),
    )

    detail_num = models.CharField(max_length=20, verbose_name='明细信息行号', db_index=True)
    category = models.CharField(max_length=60, verbose_name='单据类型')
    ori_creator = models.CharField(max_length=60, verbose_name='创建人')
    order_id = models.CharField(max_length=60, verbose_name='单据编号', db_index=True)
    date = models.DateTimeField(max_length=60, verbose_name='日期')
    owner = models.CharField(max_length=50, verbose_name='货主')
    department = models.CharField(max_length=30, verbose_name='销售部门')
    goods_id = models.CharField(max_length=60, verbose_name='物料编码', db_index=True)
    goods_name = models.CharField(max_length=60, verbose_name='物料名称')
    goods_memo = models.CharField(max_length=200, verbose_name='物料说明')
    batch_num = models.CharField(max_length=60, verbose_name='批号')
    quantity = models.IntegerField(verbose_name='实退数量')
    warehouse = models.CharField(max_length=60, verbose_name='仓库', db_index=True)
    memorandum = models.CharField(null=True, blank=True, max_length=200, verbose_name='备注')
    price = models.FloatField(verbose_name='单价')
    amount = models.FloatField(verbose_name='价税合计')

    order_status = models.SmallIntegerField(choices=ORDER_STATUS, default=1, verbose_name='状态')
    mistake_tag = models.SmallIntegerField(choices=MISTAKE_TAG, default=0, verbose_name='问题原因')

    class Meta:
        verbose_name = 'oms-原始采购退料单'
        verbose_name_plural = verbose_name
        unique_together = ('detail_num', 'order_id')
        db_table = 'oms_ic_oripurrefund'

    def __str__(self):
        return str(self.order_id)


class OriPRUnhandle(OriPurRefund):
    VERIFY_FIELD = ['detail_num', 'category', 'ori_creator', 'order_id', 'date', 'owner', 'department', 'goods_id',
                    'goods_name', 'goods_memo', 'batch_num', 'quantity', 'warehouse', 'memorandum', 'price', 'amount']

    class Meta:
        verbose_name = 'oms-原始未递交采购退料单'
        verbose_name_plural = verbose_name
        proxy = True


    @classmethod
    def verify_mandatory(cls, columns_key):
        for i in cls.VERIFY_FIELD:
            if i not in columns_key:
                return 'verify_field error, must have mandatory field: "{}""'.format(i)
        else:
            return None


# 原始直接调拨单
class OriAllocation(BaseModel):
    ORDER_STATUS = (
        (0, '已取消'),
        (1, '未递交'),
        (2, '已递交'),
    )
    MISTAKE_TAG = (
        (0, '正常'),
        (1, '货数被并'),
        (2, '导入重复'),
        (3, '工厂非法'),
        (4, '货品非法'),
        (5, '其他错误'),
    )

    detail_num = models.CharField(max_length=20, verbose_name='明细信息行号', db_index=True)
    order_id = models.CharField(max_length=60, verbose_name='单据编号', db_index=True)
    category = models.CharField(max_length=60, verbose_name='单据类型')
    trans_in = models.CharField(max_length=50, verbose_name='调入库存组织')
    date = models.DateTimeField(max_length=60, verbose_name='日期')
    trans_out = models.CharField(max_length=50, verbose_name='调出库存组织')
    department = models.CharField(max_length=30, verbose_name='销售部门')
    memorandum = models.CharField(null=True, blank=True, max_length=200, verbose_name='备注')
    ori_creator = models.CharField(max_length=60, verbose_name='创建人')
    goods_id = models.CharField(max_length=60, verbose_name='物料编码', db_index=True)
    goods_name = models.CharField(max_length=60, verbose_name='物料名称')
    goods_size = models.CharField(max_length=60, verbose_name='规格型号')
    batch_num = models.CharField(max_length=60, verbose_name='批号')
    quantity = models.IntegerField(verbose_name='调拨数量')
    warehouse_out = models.CharField(max_length=60, verbose_name='调出仓库', db_index=True)
    warehouse_in = models.CharField(max_length=60, verbose_name='调入仓库', db_index=True)
    produce_time = models.DateTimeField(max_length=60, verbose_name='生产日期')
    expiry_time = models.DateTimeField(max_length=60, verbose_name='有效期至')
    stockin_time = models.DateTimeField(max_length=60, verbose_name='入库日期')
    customer = models.CharField(max_length=50, verbose_name='客户')

    order_status = models.SmallIntegerField(choices=ORDER_STATUS, default=1, verbose_name='状态')
    mistake_tag = models.SmallIntegerField(choices=MISTAKE_TAG, default=0, verbose_name='问题原因')

    class Meta:
        verbose_name = 'oms-原始直接调拨单'
        verbose_name_plural = verbose_name
        unique_together = ('detail_num', 'order_id')
        db_table = 'oms_ic_oriallocation'

    def __str__(self):
        return str(self.order_id)


class OriALUnhandle(OriAllocation):
    VERIFY_FIELD = ['detail_num', 'order_id', 'category', 'trans_in', 'date', 'trans_out', 'department', 'memorandum',
                    'ori_creator', 'goods_id', 'goods_name', 'goods_size', 'batch_num', 'quantity', 'warehouse_out',
                    'warehouse_in', 'produce_time', 'expiry_time', 'stockin_time', 'customer']

    class Meta:
        verbose_name = 'oms-原始未递交直接调拨单'
        verbose_name_plural = verbose_name
        proxy = True


    @classmethod
    def verify_mandatory(cls, columns_key):
        for i in cls.VERIFY_FIELD:
            if i not in columns_key:
                return 'verify_field error, must have mandatory field: "{}""'.format(i)
        else:
            return None


# 原始盘盈单
class OriSurplus(BaseModel):
    ORDER_STATUS = (
        (0, '已取消'),
        (1, '未递交'),
        (2, '已递交'),
    )
    MISTAKE_TAG = (
        (0, '正常'),
        (1, '货数被并'),
        (2, '导入重复'),
        (3, '工厂非法'),
        (4, '货品非法'),
        (5, '其他错误'),
    )

    detail_num  = models.CharField(max_length=20, verbose_name='明细信息行号', db_index=True)
    order_id = models.CharField(max_length=60, verbose_name='单据编号', db_index=True)
    category = models.CharField(max_length=60, verbose_name='单据类型')
    date = models.DateTimeField(max_length=60, verbose_name='日期')
    ori_creator = models.CharField(max_length=60, verbose_name='创建人')
    owner = models.CharField(max_length=50, verbose_name='货主')
    memorandum = models.CharField(null=True, blank=True, max_length=200, verbose_name='备注')
    goods_id = models.CharField(max_length=60, verbose_name='物料编码', db_index=True)
    goods_name = models.CharField(max_length=60, verbose_name='物料名称')
    goods_size = models.CharField(max_length=60, verbose_name='规格型号')
    stock = models.IntegerField(verbose_name='账存数量')
    check = models.IntegerField(verbose_name='盘点数量')
    quantity = models.IntegerField(verbose_name='盘盈数量')
    warehouse = models.CharField(max_length=60, verbose_name='仓库', db_index=True)
    batch_num = models.CharField(max_length=60, verbose_name='批号')
    produce_time = models.DateTimeField(max_length=60, verbose_name='生产日期')
    expiry_time = models.DateTimeField(max_length=60, verbose_name='到期日')

    order_status = models.SmallIntegerField(choices=ORDER_STATUS, default=1, verbose_name='状态')
    mistake_tag = models.SmallIntegerField(choices=MISTAKE_TAG, default=0, verbose_name='问题原因')

    class Meta:
        verbose_name = 'oms-原始盘盈单'
        verbose_name_plural = verbose_name
        unique_together = ('detail_num', 'order_id')
        db_table = 'oms_ic_orisurplus'

    def __str__(self):
        return str(self.order_id)


class OriSUUnhandle(OriSurplus):
    VERIFY_FIELD = ['detail_num', 'order_id', 'category', 'date', 'ori_creator', 'owner', 'memorandum', 'goods_id',
                    'goods_name', 'goods_size', 'stock', 'check', 'quantity', 'warehouse', 'batch_num', 'produce_time',
                    'expiry_time']

    class Meta:
        verbose_name = 'oms-原始未递交盘盈单'
        verbose_name_plural = verbose_name
        proxy = True


    @classmethod
    def verify_mandatory(cls, columns_key):
        for i in cls.VERIFY_FIELD:
            if i not in columns_key:
                return 'verify_field error, must have mandatory field: "{}""'.format(i)
        else:
            return None


# 原始盘亏单
class OirLoss(BaseModel):
    ORDER_STATUS = (
        (0, '已取消'),
        (1, '未递交'),
        (2, '已递交'),
    )
    MISTAKE_TAG = (
        (0, '正常'),
        (1, '货数被并'),
        (2, '导入重复'),
        (3, '工厂非法'),
        (4, '货品非法'),
        (5, '其他错误'),
    )

    detail_num  = models.CharField(max_length=20, verbose_name='明细信息行号', db_index=True)
    order_id = models.CharField(max_length=60, verbose_name='单据编号', db_index=True)
    category = models.CharField(max_length=60, verbose_name='单据类型')
    date = models.DateTimeField(max_length=60, verbose_name='日期')
    ori_creator = models.CharField(max_length=60, verbose_name='创建人')
    owner = models.CharField(max_length=50, verbose_name='货主')
    memorandum = models.CharField(null=True, blank=True, max_length=200, verbose_name='备注')
    goods_id = models.CharField(max_length=60, verbose_name='物料编码', db_index=True)
    goods_name = models.CharField(max_length=60, verbose_name='物料名称')
    goods_size = models.CharField(max_length=60, verbose_name='规格型号')
    stock = models.IntegerField(verbose_name='账存数量')
    check = models.IntegerField(verbose_name='盘点数量')
    quantity = models.IntegerField(verbose_name='盘亏数量')
    warehouse = models.CharField(max_length=60, verbose_name='仓库', db_index=True)
    batch_num = models.CharField(max_length=60, verbose_name='批号')
    produce_time = models.DateTimeField(max_length=60, verbose_name='生产日期')
    expiry_time = models.DateTimeField(max_length=60, verbose_name='到期日')

    order_status = models.SmallIntegerField(choices=ORDER_STATUS, default=1, verbose_name='状态')
    mistake_tag = models.SmallIntegerField(choices=MISTAKE_TAG, default=0, verbose_name='问题原因')

    class Meta:
        verbose_name = 'oms-原始盘亏单'
        verbose_name_plural = verbose_name
        unique_together = ('detail_num', 'order_id')
        db_table = 'oms_ic_oriloss'

    def __str__(self):
        return str(self.order_id)


class OriLOUnhandle(OirLoss):
    VERIFY_FIELD = ['detail_num', 'order_id', 'category', 'date', 'ori_creator', 'owner', 'memorandum', 'goods_id',
                    'goods_name', 'goods_size', 'stock', 'check', 'quantity', 'warehouse', 'batch_num', 'produce_time',
                    'expiry_time']

    class Meta:
        verbose_name = 'oms-原始未递交盘亏单'
        verbose_name_plural = verbose_name
        proxy = True


    @classmethod
    def verify_mandatory(cls, columns_key):
        for i in cls.VERIFY_FIELD:
            if i not in columns_key:
                return 'verify_field error, must have mandatory field: "{}""'.format(i)
        else:
            return None

