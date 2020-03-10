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
from apps.base.company.models import CompanyInfo
from apps.wms.stock.models import DeptStockInfo
from apps.base.warehouse.models import WarehouseGeneral, WarehouseVirtual


class VAllotSOInfo(BaseModel):
    ORDER_STATUS = (
        (0, '已取消'),
        (1, '待审核'),
        (2, '待分配'),
        (3, '已完成'),
    )
    ERROR_LIST = (
        (0, '正常'),
        (1, '调拨数量不足'),
        (2, '更新虚拟库存错误'),
        (3, '单据保存出错'),
        (4, '保存部门仓失败'),
        (5, '保存实仓失败'),
        (6, '保存部门仓失败'),
        (7, '部门没有此货品'),
    )
    CATEGORY = (
        (0, '计划出库'),
        (1, '临时出库'),
    )
    dept_stock = models.ForeignKey(DeptStockInfo, on_delete=models.CASCADE, verbose_name='源部门仓')
    order_id = models.CharField(max_length=50, unique=True, verbose_name='单据编号')
    order_category = models.SmallIntegerField(choices=CATEGORY, default=0, verbose_name='单据类型')
    department = models.ForeignKey(DepartmentInfo, on_delete=models.CASCADE, verbose_name='部门')
    warehouse = models.ForeignKey(WarehouseGeneral, on_delete=models.CASCADE, related_name='a_ware', verbose_name='仓库')
    vwarehouse = models.ForeignKey(WarehouseVirtual, on_delete=models.CASCADE, related_name='a_vware', verbose_name='部门仓')
    goods_id = models.CharField(max_length=50, verbose_name='物料编码')
    goods_name = models.ForeignKey(GoodsInfo, on_delete=models.CASCADE, verbose_name='物料名称')
    quantity = models.IntegerField(verbose_name='分配总量')
    undistributed = models.IntegerField(verbose_name='待分配数量')
    memorandum = models.CharField(null=True, blank=True, max_length=300, verbose_name='备注')

    mistake_tag = models.SmallIntegerField(choices=ERROR_LIST, default=0, verbose_name='错误原因')
    order_status = models.SmallIntegerField(choices=ORDER_STATUS, default=1, verbose_name='状态')

    class Meta:
        verbose_name = 'oms-a-部门出库单查询'
        verbose_name_plural = verbose_name
        db_table = 'oms_vallot_stockout'

    def dept_stock_quantity(self):
        return self.dept_stock.quantity
    dept_stock_quantity.short_description = '对应部门仓库存'

    def __str__(self):
        return str(self.order_id)


class VASOCheck(VAllotSOInfo):

    class Meta:
        verbose_name = 'oms-a-未审核部门出库单'
        verbose_name_plural = verbose_name
        proxy = True

    def __str__(self):
        return str(self.order_id)


class VASOHandle(VAllotSOInfo):
    class Meta:
        verbose_name = 'oms-a-未分配部门出库单'
        verbose_name_plural = verbose_name
        proxy = True

    def __str__(self):
        return str(self.order_id)


class VAllotSIInfo(BaseModel):
    ORDER_STATUS = (
        (0, '已取消'),
        (1, '未审核'),
        (2, '未处理'),
        (3, '已完成'),
    )

    MISTAKE_TAG = (
        (0, '正常'),
        (1, '虚拟入库超出了出库数'),
        (2, '对应虚拟入库出错'),
        (3, '虚拟仓库存增加出错，需要联系管理员处理'),
        (4, '实仓可调拨库存数量错误'),
        (5, '查不到实仓可调拨货品'),
        (5, '实仓可调拨保存错误'),

    )
    CATEGORY = (
        (0, '计划入库'),
        (1, '临时入库'),
    )
    va_stockin = models.ForeignKey(VAllotSOInfo, on_delete=models.CASCADE, verbose_name='关联入库单')
    order_id = models.CharField(max_length=60, verbose_name='单据编号', unique=True, db_index=True)
    order_category = models.SmallIntegerField(choices=CATEGORY, default=0, verbose_name='单据类型')
    ori_department = models.ForeignKey(DepartmentInfo, on_delete=models.CASCADE, related_name='ori_dept',
                                       verbose_name='源部门')
    ori_vwarehouse = models.ForeignKey(WarehouseVirtual, on_delete=models.CASCADE, related_name='ori_vware', verbose_name='源部门仓')
    department = models.ForeignKey(DepartmentInfo, on_delete=models.CASCADE, verbose_name='目的部门')
    goods_id = models.CharField(max_length=60, verbose_name='物料编码', db_index=True)
    goods_name = models.ForeignKey(GoodsInfo, on_delete=models.CASCADE, verbose_name='物料名称')
    quantity = models.IntegerField(verbose_name='入库数量')
    warehouse = models.ForeignKey(WarehouseGeneral, on_delete=models.CASCADE, related_name='asi_ware', verbose_name='仓库')
    vwarehouse = models.ForeignKey(WarehouseVirtual, on_delete=models.CASCADE, related_name='asi_vware', verbose_name='目的部门仓')
    memorandum = models.CharField(max_length=300, null=True, blank=True, verbose_name='备注')
    order_status = models.SmallIntegerField(choices=ORDER_STATUS, default=1, verbose_name='订单状态', db_index=True)
    mistake_tag = models.SmallIntegerField(choices=MISTAKE_TAG, default=0, verbose_name='错误标识')

    class Meta:
        verbose_name = 'oms-a-部门入库单查询'
        verbose_name_plural = verbose_name
        db_table = 'oms_vallot_stockin'

    def __str__(self):
        return str(self.order_id)


class VASICheck(VAllotSIInfo):
    VERIFY_FIELD = ['order_category', 'department', 'quantity', 'va_stockin']

    class Meta:
        verbose_name = 'oms-a-未审核部门入库单'
        verbose_name_plural = verbose_name
        proxy = True

    def __str__(self):
        return str(self.order_id)

    @classmethod
    def verify_mandatory(cls, columns_key):
        for i in cls.VERIFY_FIELD:
            if i not in columns_key:
                return 'verify_field error, must have mandatory field: "{}""'.format(i)
        else:
            return None


class VASIMine(VAllotSIInfo):

    class Meta:
        verbose_name = 'oms-a-未处理部门入库单'
        verbose_name_plural = verbose_name
        proxy = True

    def __str__(self):
        return str(self.order_id)