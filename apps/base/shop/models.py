# -*- coding: utf-8 -*-
# @Time    : 2019/11/19 21:36
# @Author  : Hann
# @Site    :
# @File    : adminx.py
# @Software: PyCharm

from db.base_model import BaseModel
from django.db import models

from apps.base.company.models import MineInfo
from apps.base.department.models import CentreInfo


class PlatformInfo(BaseModel):

    ORDER_STATUS = (
        (0, '取消'),
        (1, '正常'),
    )
    p_name = models.CharField(unique=True, max_length=60, verbose_name='平台名称')
    order_status = models.SmallIntegerField(choices=ORDER_STATUS, default=1, verbose_name='单据状态')

    class Meta:
        verbose_name = 'B-店铺-平台'
        verbose_name_plural = verbose_name
        db_table = 'base_shop_platform'

    def __str__(self):
        return self.p_name


class ShopInfo(BaseModel):
    ORDER_STATUS = (
        (0, '取消'),
        (1, '正常'),
    )

    name = models.CharField(unique=True, max_length=60, verbose_name='店铺名称')
    shop_id = models.CharField(unique=True, max_length=30, verbose_name='店铺ID', db_index=True)
    platform = models.ForeignKey(PlatformInfo, on_delete=models.CASCADE, verbose_name='平台', null=True, blank=True)
    centre = models.ForeignKey(CentreInfo, on_delete=models.CASCADE, verbose_name='部门')
    company = models.ForeignKey(MineInfo, on_delete=models.SET_NULL, verbose_name='公司', null=True, blank=True)
    order_status = models.SmallIntegerField(choices=ORDER_STATUS, default=1, verbose_name='单据状态')

    class Meta:
        verbose_name = 'B-店铺-店铺'
        verbose_name_plural = verbose_name
        db_table = 'base_shop_shop'

    def __str__(self):
        return self.name


    @classmethod
    def verify_mandatory(cls, columns_key):
        VERIFY_FIELD = ['name', 'shop_id', 'centre']

        for i in VERIFY_FIELD:
            if i not in columns_key:
                return 'verify_field error, must have mandatory field: "{}""'.format(i)
        else:
            return None


