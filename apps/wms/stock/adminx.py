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


from .models import StockInfo, DeptStockInfo, MyDeptStock, TransDeptStock
# from apps.oms.predistribution.models import Undistribution
from apps.base.relationship.models import DeptToVW, DeptToW
from apps.base.warehouse.models import WarehouseVirtual
from apps.oms.allot.models import VASOCheck


class VASOCheckInline(object):
    model = VASOCheck
    exclude = ['order_id', 'is_delete', 'creator', 'order_status', 'mistake_tag', 'is_delete', 'goods_id', 'goods_name',
               'department', 'warehouse', 'vwarehouse', 'undistributed']

    extra = 1
    style = 'table'

    def queryset(self):
        queryset = super(VASOCheckInline, self).queryset()
        queryset = queryset.filter(is_delete=0, order_status=1)
        return queryset


class StockInfoAdmin(object):
    list_display = ['goods_name', 'goods_id', 'warehouse', 'quantity', 'undistributed', 'memorandum', 'order_status']
    list_filter = ['goods_name__goods_name', 'goods_id', 'warehouse__warehouse_name', 'quantity', 'order_status']
    readonly_fields = ['goods_name', 'goods_id', 'warehouse', 'quantity', 'undistributed', 'order_status']
    search_fields = ['goods_id']
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
            vwarehouse = DeptToW.objects.filter(department=department)
            if vwarehouse.exists():
                self.formsets[0].forms[i].instance.vwarehouse = vwarehouse[0].warehouse

            else:
                self.message_user("%s 没有设置部门关联的仓库。预分配生成失败" % department, "error")
                continue

        super().save_related()


class MyDeptStockAdmin(object):
    list_display = ['department', 'goods_name', 'goods_id', 'vwarehouse', 'warehouse', 'quantity', 'memorandum', 'order_status']
    list_filter = ['goods_name__goods_name', 'goods_id', 'warehouse__warehouse_name', 'vwarehouse__warehouse_name', 'order_status']
    readonly_fields = ['goods_name', 'goods_id', 'warehouse', 'vwarehouse', 'quantity', 'order_status']
    search_fields = ['goods_id', 'department__name']
    relfield_style = 'fk-ajax'

    form_layout = [
        Fieldset('存货信息',
                 'goods_name', 'vwarehouse', 'warehouse', 'quantity'),
        Fieldset('选填信息',
                 'memorandum'),
        Fieldset(None,
                 'creator', 'order_status', 'is_delete', 'goods_id', **{"style": "display:None"}),
    ]

    def queryset(self):
        queryset = super(MyDeptStockAdmin, self).queryset()
        _q_vwarehouse = DeptToVW.objects.filter(department=self.request.user.department)
        if _q_vwarehouse:
            vwarehouse = _q_vwarehouse[0].warehouse
            queryset = queryset.filter(is_delete=0, vwarehouse=vwarehouse)
        else:
            queryset = queryset.filter(id=0)
            self.message_user("没有设置部门，请联系管理员设置部门", "error")
        return queryset


class TransDeptStockAdmin(object):
    list_display = ['department', 'goods_name', 'goods_id', 'vwarehouse', 'warehouse', 'quantity', 'memorandum',
                    'order_status']
    list_filter = ['goods_name__goods_name', 'goods_id', 'warehouse__warehouse_name', 'vwarehouse__warehouse_name',
                   'order_status']
    search_fields = ['goods_id', 'department__name']
    readonly_fields = ['goods_name', 'goods_id', 'warehouse', 'vwarehouse', 'quantity', 'order_status', 'department']
    inlines = [VASOCheckInline,]
    list_editable = ['memorandum']
    relfield_style = 'fk-ajax'

    form_layout = [
        Fieldset('存货信息',
                 'goods_name', 'vwarehouse', 'department', 'warehouse', 'quantity'),
        Fieldset('选填信息',
                 'memorandum'),
        Fieldset(None,
                 'creator', 'order_status', 'is_delete', 'goods_id','create_time', 'update_time', **{"style": "display:None"}),
    ]

    def queryset(self):
        queryset = super(TransDeptStockAdmin, self).queryset()
        _q_vwarehouse = WarehouseVirtual.objects.filter(warehouse_name='正品待分仓')
        if _q_vwarehouse:
            vwarehouse = _q_vwarehouse[0]
            queryset = queryset.filter(is_delete=0, vwarehouse=vwarehouse, quantity__gt=0).order_by('goods_id', '-quantity')
        else:
            queryset = queryset.filter(id=0)
        return queryset

    def save_related(self):

        for i in range(self.formsets[0].forms.__len__()):
            request = self.request
            obj = self.formsets[0].forms[i].instance
            if not obj.order_id:
                prefix = "AO"
                serial_number = str(datetime.datetime.now()).replace("-", "").replace(" ", "").replace(":", "").replace(".", "")[:12]
                suffix = 100 + i
                order_id = prefix + str(serial_number) + str(suffix) + "A"
                obj.order_id = order_id

            obj.creator = request.user.username
            obj.goods_name = self.org_obj.goods_name
            obj.goods_id = self.org_obj.goods_id
            obj.department = self.org_obj.department
            obj.warehouse = self.org_obj.warehouse
            obj.vwarehouse = self.org_obj.vwarehouse
            obj.undistributed = obj.quantity

        super().save_related()


class DeptStockInfoAdmin(object):
    list_display = ['department', 'goods_name', 'goods_id', 'vwarehouse', 'warehouse', 'quantity', 'memorandum', 'order_status']
    list_filter = ['goods_name__goods_name', 'goods_id', 'warehouse__warehouse_name', 'vwarehouse__warehouse_name', 'order_status']
    readonly_fields = ['goods_name', 'goods_id', 'warehouse', 'vwarehouse', 'quantity', 'order_status']
    search_fields = ['goods_id', 'department__name']
    relfield_style = 'fk-ajax'

    form_layout = [
        Fieldset('存货信息',
                 'goods_name', 'vwarehouse', 'warehouse', 'quantity'),
        Fieldset('选填信息',
                 'memorandum'),
        Fieldset(None,
                 'creator', 'order_status', 'is_delete', 'goods_id', **{"style": "display:None"}),
    ]


xadmin.site.register(StockInfo, StockInfoAdmin)
xadmin.site.register(MyDeptStock, MyDeptStockAdmin)
xadmin.site.register(TransDeptStock, TransDeptStockAdmin)
xadmin.site.register(DeptStockInfo, DeptStockInfoAdmin)