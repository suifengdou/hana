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
from apps.base.relationship.models import DeptToVW, DeptToW
from apps.base.warehouse.models import WarehouseVirtual
from apps.oms.allot.models import VASOCheck


# 快速生成虚拟调拨出库单
class AOCreateAction(BaseActionView):
    action_name = "submit_create_oa"
    description = "快速生成库存到出库单"
    model_perm = 'change'
    icon = "fa fa-check-square-o"

    modify_models_batch = False

    @filter_hook
    def do_action(self, queryset):
        if not self.has_change_permission():
            raise PermissionDenied
        n = queryset.count()
        if n:
            if self.modify_models_batch:
                self.log('change',
                         '批量审核了 %(count)d %(items)s.' % {"count": n, "items": model_ngettext(self.opts, n)})
                queryset.update(status=2)
            else:
                i = 0
                for obj in queryset:
                    i += 1
                    self.log('change', '', obj)
                    order_so = VASOCheck()

                    prefix = "AO"
                    serial_number = str(datetime.datetime.now()).replace("-", "").replace(" ", "").replace(":","").replace(".", "")[:12]
                    suffix = 1000 + i
                    order_id = prefix + str(serial_number) + str(suffix)
                    order_so.order_id = order_id

                    order_so.creator = self.request.user.username
                    order_so.goods_name = obj.goods_name
                    order_so.goods_id = obj.goods_id
                    order_so.centre = obj.centre
                    order_so.warehouse = obj.warehouse
                    order_so.vwarehouse = obj.vwarehouse
                    order_so.undistributed = obj.quantity
                    order_so.quantity = obj.quantity
                    order_so.dept_stock = obj
                    try:
                        order_so.save()
                    except Exception as e:
                        self.message_user("%s 创建虚拟出库单出错, %s" % (obj.order_id, e), "error")
                        continue

            self.message_user("成功生成 %(count)d %(items)s." % {"count": n, "items": model_ngettext(self.opts, n)},
                              'success')

        return None


class VASOCheckInline(object):
    model = VASOCheck
    exclude = ['order_id', 'is_delete', 'creator', 'order_status', 'mistake_tag', 'is_delete', 'goods_id', 'goods_name',
               'warehouse', 'vwarehouse', 'undistributed', 'centre']

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
    batch_data = True
    delivery_ids = []

    def post(self, request, *args, **kwargs):
        delivery_ids = request.POST.get('ids', None)
        if delivery_ids is not None:
            if " " in delivery_ids:
                delivery_ids = delivery_ids.split(" ")
                for i in delivery_ids:
                    if not re.match(r'^.{3,30}$', i):
                        self.message_user('%s包含错误的货品编号，请检查' % str(delivery_ids), 'error')
                        break

                self.delivery_ids = delivery_ids
                self.queryset()

        return super(StockInfoAdmin, self).post(request, *args, **kwargs)

    def queryset(self):
        queryset = super(StockInfoAdmin, self).queryset()

        if self.delivery_ids:
            queryset = queryset.filter(is_delete=0, goods_id__in=self.delivery_ids)
        else:
            queryset = queryset.filter(is_delete=0)
        return queryset

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
            centre = self.formsets[0].forms[i].instance.department.centre
            vwarehouse = DeptToW.objects.filter(department=centre)
            if vwarehouse.exists():
                self.formsets[0].forms[i].instance.vwarehouse = vwarehouse[0].warehouse

            else:
                self.message_user("%s 没有设置部门关联的仓库。预分配生成失败" % centre, "error")
                continue

        super().save_related()


class MyDeptStockAdmin(object):
    list_display = ['centre', 'goods_name', 'goods_id', 'vwarehouse', 'warehouse', 'quantity', 'memorandum', 'order_status']
    list_filter = ['goods_name__goods_name', 'goods_id', 'warehouse__warehouse_name', 'vwarehouse__warehouse_name', 'order_status']
    readonly_fields = ['goods_name', 'goods_id', 'warehouse', 'vwarehouse', 'quantity', 'order_status', 'centre',]
    search_fields = ['goods_id', 'centre__name']
    relfield_style = 'fk-ajax'

    form_layout = [
        Fieldset('存货信息',
                 'goods_name', 'vwarehouse', 'warehouse', 'quantity', 'centre',),
        Fieldset('选填信息',
                 'memorandum'),
        Fieldset(None,
                 'creator', 'order_status', 'is_delete', 'goods_id', **{"style": "display:None"}),
    ]
    batch_data = True
    delivery_ids = []

    def post(self, request, *args, **kwargs):
        delivery_ids = request.POST.get('ids', None)
        if delivery_ids is not None:
            if " " in delivery_ids:
                delivery_ids = delivery_ids.split(" ")
                for i in delivery_ids:
                    if not re.match(r'^.{3,30}$', i):
                        self.message_user('%s包含错误的货品编号，请检查' % str(delivery_ids), 'error')
                        break

                self.delivery_ids = delivery_ids
                self.queryset()

        return super(MyDeptStockAdmin, self).post(request, *args, **kwargs)

    def queryset(self):
        queryset = super(MyDeptStockAdmin, self).queryset()
        _q_vwarehouse = DeptToVW.objects.filter(centre=self.request.user.department.centre)
        if _q_vwarehouse:
            vwarehouse = _q_vwarehouse[0].warehouse
        else:
            queryset = queryset.filter(id=0)
            self.message_user("没有设置部门，请联系管理员设置部门", "error")
            return queryset
        if self.delivery_ids:
            queryset = queryset.filter(is_delete=0, goods_id__in=self.delivery_ids, vwarehouse=vwarehouse)
        else:
            queryset = queryset.filter(is_delete=0, vwarehouse=vwarehouse)
        return queryset


class TransDeptStockAdmin(object):
    list_display = ['centre', 'goods_name', 'goods_id', 'vwarehouse', 'warehouse', 'quantity', 'memorandum',
                    'order_status']
    list_filter = ['goods_name__goods_name', 'goods_id', 'warehouse__warehouse_name', 'vwarehouse__warehouse_name',
                   'order_status']
    search_fields = ['goods_id', 'department__name']
    readonly_fields = ['goods_name', 'goods_id', 'warehouse', 'vwarehouse', 'quantity', 'order_status', 'centre']
    inlines = [VASOCheckInline, ]
    actions = [AOCreateAction, ]
    list_editable = ['memorandum']
    relfield_style = 'fk-ajax'

    form_layout = [
        Fieldset('存货信息',
                 'goods_name', 'vwarehouse', 'centre', 'warehouse', 'quantity'),
        Fieldset('选填信息',
                 'memorandum'),
        Fieldset(None,
                 'creator', 'order_status', 'is_delete', 'goods_id', **{"style": "display:None"}),
    ]
    batch_data = True
    special_so = True
    delivery_ids = []

    def post(self, request, *args, **kwargs):
        delivery_ids = request.POST.get('ids', None)
        special_tag = request.POST.get('special_tag', None)
        if special_tag:
            _q_vwarehouse = WarehouseVirtual.objects.filter(warehouse_name='正品待分仓')
            if _q_vwarehouse:
                vwarehouse = _q_vwarehouse[0]
                _q_warehouse = DeptToW.objects.all()
                warehouse_list = [warehouse.warehouse for warehouse in _q_warehouse]
                queryset = TransDeptStock.objects.filter(warehouse__in=warehouse_list, vwarehouse=vwarehouse)
                n = queryset.count()
                if n:
                    i = 0
                    for obj in queryset:
                        if obj.quantity == 0:
                            n -= 1
                            continue
                        i += 1
                        self.log('change', '', obj)
                        order_so = VASOCheck()

                        prefix = "AO"
                        serial_number = str(datetime.datetime.now()).replace("-", "").replace(" ", "").replace(":",
                                                                                                               "").replace(
                            ".", "")[:12]
                        suffix = 1000 + i
                        order_id = prefix + str(serial_number) + str(suffix)
                        order_so.order_id = order_id

                        order_so.creator = self.request.user.username
                        order_so.goods_name = obj.goods_name
                        order_so.goods_id = obj.goods_id
                        order_so.centre = obj.centre
                        order_so.warehouse = obj.warehouse
                        order_so.vwarehouse = obj.vwarehouse
                        order_so.undistributed = obj.quantity
                        order_so.quantity = obj.quantity
                        order_so.dept_stock = obj
                        try:
                            order_so.save()
                        except Exception as e:
                            self.message_user("%s 创建虚拟出库单出错, %s" % (obj.order_id, e), "error")
                            continue

                self.message_user("成功生成 %(count)d %(items)s." % {"count": n, "items": model_ngettext(self.opts, n)},
                                  'success')
            else:
                self.message_user("没有设置正品待分仓", "error")
        if delivery_ids is not None:
            if " " in delivery_ids:
                delivery_ids = delivery_ids.split(" ")
                for i in delivery_ids:
                    if not re.match(r'^.{3,30}$', i):
                        self.message_user('%s包含错误的货品编号，请检查' % str(delivery_ids), 'error')
                        break

                self.delivery_ids = delivery_ids
                self.queryset()

        return super(TransDeptStockAdmin, self).post(request, *args, **kwargs)

    def queryset(self):
        queryset = super(TransDeptStockAdmin, self).queryset()
        _q_vwarehouse = WarehouseVirtual.objects.filter(warehouse_name='正品待分仓')
        if _q_vwarehouse:
            vwarehouse = _q_vwarehouse[0]
        else:
            queryset = queryset.filter(id=0)
            self.message_user("没有设置正品待分仓", "error")
            return queryset

        if self.delivery_ids:
            queryset = queryset.filter(is_delete=0, goods_id__in=self.delivery_ids, vwarehouse=vwarehouse,  quantity__gt=0)
        else:
            queryset = queryset.filter(is_delete=0, vwarehouse=vwarehouse, quantity__gt=0)
        return queryset

    def save_related(self):

        for i in range(self.formsets[0].forms.__len__()):
            request = self.request
            obj = self.formsets[0].forms[i].instance
            if not obj.order_id:
                prefix = "AO"
                serial_number = str(datetime.datetime.now()).replace("-", "").replace(" ", "").replace(":", "").replace(".", "")[:12]
                suffix = 1000 + i
                order_id = prefix + str(serial_number) + str(suffix)
                obj.order_id = order_id

            obj.creator = request.user.username
            obj.goods_name = self.org_obj.goods_name
            obj.goods_id = self.org_obj.goods_id
            obj.centre = self.org_obj.centre
            obj.warehouse = self.org_obj.warehouse
            obj.vwarehouse = self.org_obj.vwarehouse
            obj.undistributed = obj.quantity

        super().save_related()


class DeptStockInfoAdmin(object):
    list_display = ['centre', 'goods_name', 'goods_id', 'vwarehouse', 'warehouse', 'quantity', 'memorandum', 'order_status']
    list_filter = ['centre__name', 'goods_name__goods_name', 'goods_id', 'warehouse__warehouse_name', 'vwarehouse__warehouse_name', 'order_status']
    readonly_fields = ['goods_name', 'goods_id', 'warehouse', 'vwarehouse', 'quantity', 'order_status', 'centre',]
    search_fields = ['goods_id', 'centre__name']
    relfield_style = 'fk-ajax'
    inlines = [VASOCheckInline, ]
    form_layout = [
        Fieldset('存货信息',
                 'goods_name', 'vwarehouse', 'warehouse', 'quantity', 'centre',),
        Fieldset('选填信息',
                 'memorandum'),
        Fieldset(None,
                 'creator', 'order_status', 'is_delete', 'goods_id', **{"style": "display:None"}),
    ]
    batch_data = True
    delivery_ids = []

    def post(self, request, *args, **kwargs):
        delivery_ids = request.POST.get('ids', None)
        if delivery_ids is not None:
            if " " in delivery_ids:
                delivery_ids = delivery_ids.split(" ")
                for i in delivery_ids:
                    if not re.match(r'^.{3,30}$', i):
                        self.message_user('%s包含错误的货品编号，请检查' % str(delivery_ids), 'error')
                        break

                self.delivery_ids = delivery_ids
                self.queryset()

        return super(DeptStockInfoAdmin, self).post(request, *args, **kwargs)

    def queryset(self):
        queryset = super(DeptStockInfoAdmin, self).queryset()

        if self.delivery_ids:
            queryset = queryset.filter(is_delete=0, goods_id__in=self.delivery_ids)
        else:
            queryset = queryset.filter(is_delete=0)
        return queryset

    def save_related(self):

        for i in range(self.formsets[0].forms.__len__()):
            request = self.request
            obj = self.formsets[0].forms[i].instance
            if not obj.order_id:
                prefix = "AO"
                serial_number = str(datetime.datetime.now()).replace("-", "").replace(" ", "").replace(":", "").replace(".", "")[:12]
                suffix = 1000 + i
                order_id = prefix + str(serial_number) + str(suffix)
                obj.order_id = order_id

            obj.creator = request.user.username
            obj.goods_name = self.org_obj.goods_name
            obj.goods_id = self.org_obj.goods_id
            obj.centre = self.org_obj.centre
            obj.warehouse = self.org_obj.warehouse
            obj.vwarehouse = self.org_obj.vwarehouse
            obj.undistributed = obj.quantity

        super().save_related()


xadmin.site.register(StockInfo, StockInfoAdmin)
xadmin.site.register(MyDeptStock, MyDeptStockAdmin)
xadmin.site.register(TransDeptStock, TransDeptStockAdmin)
xadmin.site.register(DeptStockInfo, DeptStockInfoAdmin)