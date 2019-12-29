# -*- coding: utf-8 -*-
# @Time    : 2019/12/2 21:35
# @Author  : Hann
# @Site    : 
# @File    : adminx.py
# @Software: PyCharm

import pandas as pd
import re, datetime, math

from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.db import router
from django.utils.encoding import force_text
from django.template.response import TemplateResponse
from django.contrib.admin.utils import get_deleted_objects


import xadmin

from xadmin.plugins.actions import BaseActionView
from xadmin.views.base import filter_hook
from xadmin.util import model_ngettext
from xadmin.layout import Fieldset


from .models import StockInfo, DeptStockInfo
from apps.oms.predistribution.models import Undistribution
from apps.base.relationship.models import DepartmentToWarehouse
from apps.oms.allot.models import VAPending


class PredistributionInline(object):
    model = Undistribution

    exclude = ['distribution_order_id', 'goods_name', 'vwarehouse', 'creator', 'order_status', 'error_tag', 'is_delete', 'goods_id']
    extra = 1
    style = 'table'

    def queryset(self):
        queryset = super(PredistributionInline, self).queryset()
        queryset = queryset.filter(is_delete=0, order_status=1)
        return queryset


class VAPendingInline(object):
    model = VAPending
    exclude = ['allot_order_id', 'is_delete', 'creator', 'order_status', 'error_tag', 'is_delete', 'goods_id', 'goods_name', 'department']
    extra = 1
    style = 'table'

    def queryset(self):
        queryset = super(VAPendingInline, self).queryset()
        queryset = queryset.filter(is_delete=0, order_status=1)
        return queryset


class StockInfoAdmin(object):
    list_display = ['goods_name', 'goods_id', 'warehouse', 'quantity', 'undistributed', 'memorandum', 'order_status']
    list_filter = ['goods_name__goods_name', 'goods_id', 'warehouse__warehouse_name', 'order_status']
    readonly_fields = ['goods_name', 'goods_id', 'warehouse', 'quantity', 'undistributed', 'order_status']
    inlines = [PredistributionInline, ]
    relfield_style = 'fk-ajax'
    form_layout = [
        Fieldset('存货信息',
                 'goods_name', 'warehouse', 'quantity', 'undistributed'),
        Fieldset('选填信息',
                 'memorandum'),
        Fieldset(None,
                 'creator', 'order_status', 'is_delete', 'goods_id', **{"style": "display:None"}),
    ]

    def save_related(self):

        for i in range(self.formsets[0].forms.__len__()):
            if not self.formsets[0].forms[i].instance.department_id:
                continue
            request = self.request
            if not self.formsets[0].forms[i].instance.distribution_order_id:
                prefix = "DO"
                serial_number = str(datetime.datetime.now())
                serial_number = int(serial_number.replace("-", "").replace(" ", "").replace(":", "").replace(".", "")) + i
                distribution_order_id = prefix + str(serial_number) + "A"
                self.formsets[0].forms[i].instance.distribution_order_id = distribution_order_id

            self.formsets[0].forms[i].instance.creator = request.user.username
            self.formsets[0].forms[i].instance.goods_name = self.org_obj.goods_name
            self.formsets[0].forms[i].instance.goods_id = self.org_obj.goods_id
            department = self.formsets[0].forms[i].instance.department
            vwarehouse = DepartmentToWarehouse.objects.filter(department=department)
            if vwarehouse.exists():
                self.formsets[0].forms[i].instance.vwarehouse = vwarehouse[0].warehouse

            else:
                self.message_user("%s 没有设置部门关联的仓库。预分配生成失败" % department, "error")
                continue

        super().save_related()


class DeptStockInfoAdmin(object):
    list_display = ['goods_name', 'goods_id', 'vwarehouse', 'warehouse', 'quantity', 'memorandum', 'order_status']
    list_filter = ['goods_name__goods_name', 'goods_id', 'warehouse__warehouse_name', 'vwarehouse__warehouse_name', 'order_status']
    readonly_fields = ['goods_name', 'goods_id', 'warehouse', 'vwarehouse', 'quantity', 'order_status']
    inlines = [VAPendingInline,]
    relfield_style = 'fk-ajax'

    form_layout = [
        Fieldset('存货信息',
                 'goods_name', 'vwarehouse', 'warehouse', 'quantity'),
        Fieldset('选填信息',
                 'memorandum'),
        Fieldset(None,
                 'creator', 'order_status', 'is_delete', 'goods_id', **{"style": "display:None"}),
    ]

    def save_related(self):

        for i in range(self.formsets[0].forms.__len__()):
            if not self.formsets[0].forms[i].instance.vwarehouse_des:
                continue
            request = self.request
            if not self.formsets[0].forms[i].instance.allot_order_id:
                prefix = "AO"
                serial_number = str(datetime.datetime.now())
                serial_number = int(serial_number.replace("-", "").replace(" ", "").replace(":", "").replace(".", "")) + i
                allot_order_id = prefix + str(serial_number) + "A"
                self.formsets[0].forms[i].instance.allot_order_id = allot_order_id
                vwarehouse = self.formsets[0].forms[i].instance.vwarehouse_ori
                department = DepartmentToWarehouse.objects.filter(warehouse=vwarehouse.vwarehouse)
                if department:
                    self.formsets[0].forms[i].instance.department = department[0].department

            self.formsets[0].forms[i].instance.creator = request.user.username
            self.formsets[0].forms[i].instance.goods_name = self.org_obj.goods_name
            self.formsets[0].forms[i].instance.goods_id = self.org_obj.goods_id

        super().save_related()


xadmin.site.register(StockInfo, StockInfoAdmin)
xadmin.site.register(DeptStockInfo, DeptStockInfoAdmin)