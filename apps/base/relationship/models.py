# -*- coding: utf-8 -*-
# @Time    : 2019/11/19 20:14
# @Author  : Hann
# @Site    :
# @File    : adminx.py
# @Software: PyCharm

from db.base_model import BaseModel
from django.db import models

from apps.base.goods.models import BarCodeInfo, GoodsInfo, SeriesInfo
from apps.base.company.models import ManuInfo
from apps.base.department.models import CentreInfo
from apps.base.warehouse.models import WarehouseVirtual, WarehouseInfo


class DeptToW(BaseModel):
    ORDER_STATUS = (
        (0, '取消'),
        (1, '正常'),
    )
    centre = models.ForeignKey(CentreInfo, models.CASCADE, verbose_name='中心名称')
    warehouse = models.ForeignKey(WarehouseInfo, models.CASCADE, verbose_name='实物仓库')
    order_status = models.SmallIntegerField(choices=ORDER_STATUS, default=1, verbose_name='单据状态')

    class Meta:
        unique_together = ('centre', 'warehouse')
        verbose_name = 'B-关联-部门2实物仓库'
        verbose_name_plural = verbose_name
        db_table = 'base_rel_dept2w'

    @classmethod
    def verify_mandatory(cls, columns_key):
        VERIFY_FIELD = ['centre', 'warehouse']

        for i in VERIFY_FIELD:
            if i not in columns_key:
                return 'verify_field error, must have mandatory field: "{}""'.format(i)
        else:
            return None


class DeptToVW(BaseModel):
    ORDER_STATUS = (
        (0, '取消'),
        (1, '正常'),
    )
    centre = models.OneToOneField(CentreInfo, models.CASCADE, verbose_name='中心名称')
    warehouse = models.ForeignKey(WarehouseVirtual, models.CASCADE, verbose_name='虚拟仓库')
    order_status = models.SmallIntegerField(choices=ORDER_STATUS, default=1, verbose_name='单据状态')

    class Meta:
        unique_together = ('centre', 'warehouse')
        verbose_name = 'B-关联-部门2虚拟仓库'
        verbose_name_plural = verbose_name
        db_table = 'base_rel_dept2vw'

    @classmethod
    def verify_mandatory(cls, columns_key):
        VERIFY_FIELD = ['centre', 'warehouse']

        for i in VERIFY_FIELD:
            if i not in columns_key:
                return 'verify_field error, must have mandatory field: "{}""'.format(i)
        else:
            return None

