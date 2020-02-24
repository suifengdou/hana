# -*- coding:  utf-8 -*-
# @Time    :  2019/5/11 13: 47
# @Author  :  Hann
# @Site    :
# @File    :  models.py
# @Software:  PyCharm

from django.db import models
import django.utils.timezone as timezone

from db.base_model import BaseModel


class WarehouseInfo(BaseModel):
    STATUS = (
        (0, '停用'),
        (1, '正常'),
    )
    CATEGORY = (
        (0, '普通仓库'),
        (1, '工厂仓库'),
        (2, '残品仓库'),
        (3, '退货仓库'),
    )
    warehouse_name = models.CharField(unique=True, max_length=60, verbose_name='仓库名称')
    warehouse_id = models.CharField(unique=True, max_length=20, verbose_name='仓库ID')
    nation = models.CharField(null=True, blank=True, max_length=50, verbose_name='国别')
    province = models.CharField(null=True, blank=True, max_length=50, verbose_name='省份')
    city = models.CharField(null=True, blank=True, max_length=50, verbose_name='城市')
    district = models.CharField(null=True, blank=True, max_length=50, verbose_name='区县')
    consignee = models.CharField(null=True, blank=True, max_length=50, verbose_name='收货人')
    mobile = models.CharField(null=True, blank=True, max_length=30, verbose_name='电话')
    address = models.CharField(null=True, blank=True, max_length=90, verbose_name='地址')
    memorandum = models.CharField(null=True, blank=True, max_length=90, verbose_name='地址')
    category = models.SmallIntegerField(choices=CATEGORY, default=0, verbose_name='仓库类型')
    order_status = models.SmallIntegerField(choices=STATUS, default=1, verbose_name='仓库状态')

    class Meta:
        verbose_name = 'BASE-仓库-实物仓库'
        verbose_name_plural = verbose_name
        db_table = 'base_wah_warehouse'

    def __str__(self):
        return self.warehouse_name

    @classmethod
    def verify_mandatory(cls, columns_key):
        VERIFY_FIELD = ['warehouse_id', 'warehouse_name']

        for i in VERIFY_FIELD:
            if i not in columns_key:
                return 'verify_field error, must have mandatory field: "{}""'.format(i)
        else:
            return None


class WarehouseGeneral(WarehouseInfo):

    class Meta:
        verbose_name = 'BASE-仓库-普通仓库'
        verbose_name_plural = verbose_name
        proxy = True


class WarehouseManu(WarehouseInfo):
    class Meta:
        verbose_name = 'BASE-仓库-工厂仓库'
        verbose_name_plural = verbose_name
        proxy = True


class WarehouseVirtual(BaseModel):
    STATUS = (
        (0, '停用'),
        (1, '正常'),
    )
    CATEGORY = (
        (0, '部门仓库'),
        (1, '全局正品'),
        (2, '全局残品'),
    )

    warehouse_name = models.CharField(unique=True, max_length=60, verbose_name='仓库名称')
    warehouse_id = models.CharField(unique=True, max_length=20, verbose_name='仓库ID')
    nation = models.CharField(null=True, blank=True, max_length=50, verbose_name='国别')
    province = models.CharField(null=True, blank=True, max_length=50, verbose_name='省份')
    city = models.CharField(null=True, blank=True, max_length=50, verbose_name='城市')
    district = models.CharField(null=True, blank=True, max_length=50, verbose_name='区县')
    consignee = models.CharField(null=True, blank=True, max_length=50, verbose_name='收货人')
    mobile = models.CharField(null=True, blank=True, max_length=30, verbose_name='电话')
    address = models.CharField(null=True, blank=True, max_length=90, verbose_name='地址')
    memorandum = models.CharField(null=True, blank=True, max_length=90, verbose_name='地址')
    category = models.SmallIntegerField(choices=CATEGORY, default=0, verbose_name='仓库类型')
    order_status = models.SmallIntegerField(choices=STATUS, default=1, verbose_name='仓库状态')

    class Meta:
        verbose_name = 'BASE-仓库-虚拟仓库'
        verbose_name_plural = verbose_name
        db_table = 'base_wah_virtual'

    def __str__(self):
        return self.warehouse_name

    @classmethod
    def verify_mandatory(cls, columns_key):
        VERIFY_FIELD = ['warehouse_id', 'warehouse_name']

        for i in VERIFY_FIELD:
            if i not in columns_key:
                return 'verify_field error, must have mandatory field: "{}""'.format(i)
        else:
            return None