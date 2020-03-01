# -*- coding: utf-8 -*-
# @Time    : 2019/12/28 14:53
# @Author  : Hann
# @Site    : 
# @File    : adminx.py
# @Software: PyCharm


import re, datetime
import pandas as pd
import xadmin

from django.core.exceptions import PermissionDenied
from django.db.models import Q, Sum, Count, Avg
from django.db import router
from django.utils.encoding import force_text
from django.template.response import TemplateResponse
from django.contrib.admin.utils import get_deleted_objects

from xadmin.plugins.actions import BaseActionView
from xadmin.views.base import filter_hook
from xadmin.util import model_ngettext
from xadmin.layout import Fieldset

from .models import VAllotSOInfo, VASOCheck, VASOHandle, VAllotSIInfo, VASICheck, VASIMine
from apps.wms.stock.models import DeptStockInfo
from apps.base.relationship.models import DeptToVW

ACTION_CHECKBOX_NAME = '_selected_action'


# 入库单关联模块，让入库单关联出库单
class VASICheckInline(object):
    model = VASICheck
    exclude = ['va_stockin', 'order_id', 'order_category', 'ori_department', 'goods_id', 'goods_name',
               'warehouse', 'order_status', 'mistake_tag', 'creator', 'ori_vwarehouse', 'is_delete', 'vwarehouse']

    extra = 1
    style = 'table'

    def queryset(self):
        queryset = super(VASICheckInline, self).queryset()
        queryset = queryset.filter(is_delete=0, order_status=1)
        return queryset


# 递交虚拟调拨单
class AOSubmitAction(BaseActionView):
    action_name = "submit_oa"
    description = "提交选中的分配单"
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
                for obj in queryset:
                    self.log('change', '', obj)
                    obj.dept_stock.quantity = obj.dept_stock.quantity - obj.quantity
                    if obj.dept_stock.quantity < 0:
                        self.message_user("%s 可调拨数量不足，修正调拨数量" % obj.order_id, "error")
                        obj.mistake_tag = 1
                        obj.save()
                        continue
                    else:
                        try:
                            obj.dept_stock.save()
                        except Exception as e:
                            self.message_user("%s 更新虚拟库存错误, %s" % (obj.order_id, e), "error")
                            obj.mistake_tag = 2
                            obj.save()
                            continue
                    obj.order_status = 2
                    obj.mistake_tag = 0
                    try:
                        obj.save()
                    except Exception as e:
                        self.message_user("%s 单据保存出错, %s" % (obj.order_id, e), "error")
                        obj.mistake_tag = 3
                        obj.save()
                        continue

            self.message_user("成功提交 %(count)d %(items)s." % {"count": n, "items": model_ngettext(self.opts, n)},
                              'success')

        return None


class VASOCheckAdmin(object):
    list_display = ['order_id', 'order_status', 'mistake_tag', 'goods_name', 'warehouse', 'vwarehouse', 'department',
                    'goods_id', 'quantity', 'undistributed', 'dept_stock_quantity', 'memorandum']
    list_filter = ['order_status', 'mistake_tag', 'goods_name__goods_name', 'warehouse__warehouse_name',
                   'vwarehouse__warehouse_name', 'department__name', 'goods_id', 'quantity']

    actions = [AOSubmitAction]
    readonly_fields = ['dept_stock', 'order_id', 'order_category', 'department', 'goods_id', 'goods_name',
                       'undistributed', 'warehouse', 'vwarehouse', 'mistake_tag', 'order_status', 'is_delete',
                       'creator', 'create_time', 'update_time']

    form_layout = [
        Fieldset('主要信息',
                  'order_id', 'goods_name', 'order_category',  'quantity', 'undistributed', 'warehouse', 'vwarehouse', 'department'),
        Fieldset('一般信息',
                 'memorandum'),
        Fieldset(None,
                 'mistake_tag', 'creator', 'order_status', 'is_delete', 'goods_id', 'dept_stock', **{"style": "display:None"}),
    ]

    def queryset(self):
        queryset = super(VASOCheckAdmin, self).queryset()
        queryset = queryset.filter(is_delete=0, order_status=1)
        return queryset

    def save_models(self):
        obj = self.new_obj
        obj.undistributed = obj.quantity
        obj.save()
        super(VASOCheckAdmin, self).save_models()

    def has_add_permission(self):
        # 禁用添加按钮
        return False


# 未分配调拨出库单
class VASOHandleAdmin(object):
    list_display = ['order_id', 'order_status', 'mistake_tag', 'goods_name', 'warehouse', 'vwarehouse', 'department',
                    'goods_id', 'quantity', 'undistributed', 'memorandum']
    list_filter = ['order_status', 'mistake_tag', 'goods_name__goods_name', 'warehouse__warehouse_name',
                   'vwarehouse__warehouse_name', 'department__name', 'goods_id', 'quantity']
    inlines = [VASICheckInline, ]
    actions = []
    readonly_fields = ['dept_stock', 'order_id', 'order_category', 'department', 'goods_id', 'goods_name', 'quantity',
                       'undistributed', 'warehouse', 'vwarehouse', 'mistake_tag', 'order_status', 'is_delete',
                       'creator', 'create_time', 'update_time']

    form_layout = [
        Fieldset('主要信息',
                  'order_id', 'goods_name', 'goods_id', 'order_category',  'quantity', 'undistributed', 'warehouse', 'vwarehouse', 'department'),
        Fieldset('一般信息',
                 'memorandum'),
        Fieldset(None,
                 'mistake_tag', 'creator', 'order_status', 'is_delete', 'dept_stock', 'create_time', 'update_time', **{"style": "display:None"}),
    ]

    def queryset(self):
        queryset = super(VASOHandleAdmin, self).queryset()
        queryset.filter(is_delete=0, order_status=2, undistributed=0).update(order_status=3)
        queryset = queryset.filter(is_delete=0, order_status=2)
        return queryset

    def save_related(self):

        for i in range(self.formsets[0].forms.__len__()):
            request = self.request
            obj = self.formsets[0].forms[i].instance
            _q_vwarehouse = DeptToVW.objects.filter(department=obj.department)
            if _q_vwarehouse.exists():
                obj.vwarehouse = _q_vwarehouse[0].warehouse

            if not obj.order_id:
                prefix = "A"
                serial_number = str(datetime.datetime.now()).replace("-", "").replace(" ", "").replace(":", "").replace(".", "")[:12]
                suffix = 100 + i
                order_id = prefix + str(serial_number) + str(suffix) + "A"
                obj.order_id = order_id


            obj.warehouse = self.org_obj.warehouse
            obj.ori_vwarehouse = self.org_obj.vwarehouse
            obj.ori_department = self.org_obj.department
            obj.creator = request.user.username
            obj.goods_name = self.org_obj.goods_name
            obj.goods_id = self.org_obj.goods_id
            obj.order_status = self.org_obj.order_status

        super().save_related()


class VAllotSOInfoAdmin(object):
    list_display = ['order_id', 'order_status', 'mistake_tag', 'goods_name', 'warehouse', 'vwarehouse', 'department',
                    'goods_id', 'quantity', 'undistributed', 'memorandum']
    list_filter = ['order_status', 'mistake_tag', 'goods_name__goods_name', 'warehouse__warehouse_name',
                   'vwarehouse__warehouse_name', 'department__name', 'goods_id', 'quantity']
    inlines = [VASICheckInline, ]
    actions = []
    readonly_fields = ['dept_stock', 'order_id', 'order_category', 'department', 'goods_id', 'goods_name', 'quantity',
                       'undistributed', 'warehouse', 'vwarehouse', 'mistake_tag', 'order_status', 'is_delete', 'creator', 'create_time', 'update_time']

    form_layout = [
        Fieldset('主要信息',
                  'order_id', 'goods_name', 'goods_id', 'order_category',  'quantity', 'undistributed', 'warehouse', 'vwarehouse', 'department'),
        Fieldset('一般信息',
                 'memorandum'),
        Fieldset(None,
                 'mistake_tag', 'creator', 'order_status', 'is_delete', 'dept_stock', **{"style": "display:None"}),
    ]

    def queryset(self):
        queryset = super(VAllotSOInfoAdmin, self).queryset()
        queryset = queryset.filter(is_delete=0, order_status=3)
        return queryset

    def has_add_permission(self):
        # 禁用添加按钮
        return False


# 审核虚拟调拨入库单
class VASICheckAction(BaseActionView):
    action_name = "check_va_si"
    description = "提交选中的分配单"
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
                for obj in queryset:
                    self.log('change', '', obj)
                    _q_dept_stock = DeptStockInfo.objects.filter(department=obj.department, goods_name=obj.goods_name,
                                                                 warehouse=obj.warehouse, vwarehouse=obj.vwarehouse)

                    if _q_dept_stock.exists():
                        dept_stock = _q_dept_stock[0]
                        dept_stock.quantity += obj.quantity
                    else:
                        dept_stock = DeptStockInfo()
                        fields = ['department', 'goods_name', 'goods_id', 'warehouse', 'vwarehouse', 'quantity']
                        for key in fields:
                            value = getattr(obj, key, None)
                            setattr(dept_stock, key, value)
                    obj.va_stockin.undistributed -= dept_stock.quantity
                    if obj.va_stockin.undistributed < 0:
                        self.message_user("%s 虚拟入库超过了对应出库数" % obj.order_id, "error")
                        obj.error_tag = 1
                        obj.save()
                    else:
                        try:
                            obj.va_stockin.save()
                        except Exception as e:
                            self.message_user("%s 更新对应虚拟入库出错, %s" % (obj.order_id, e), "error")
                            obj.mistake_tag = 2
                            obj.save()
                            continue
                    try:
                        dept_stock.save()
                    except Exception as e:
                        self.message_user("%s 单据保存出错, %s" % (obj.order_id, e), "error")
                        obj.mistake_tag = 3
                        obj.save()
                        continue
                obj.order_status = 2
                obj.mistake_tag = 0
                obj.save()
            self.message_user("成功提交 %(count)d %(items)s." % {"count": n, "items": model_ngettext(self.opts, n)},
                              'success')
        return None


# 调拨入库单审核界面
class VASICheckAdmin(object):
    list_display = ['order_id', 'order_status', 'mistake_tag', 'order_category', 'ori_department', 'department',
                    'ori_vwarehouse', 'vwarehouse', 'warehouse', 'goods_name', 'goods_id', 'quantity',
                    'memorandum', ]
    list_filter = ['order_status', 'mistake_tag', 'order_category', 'department__name', 'ori_department__name', 'ori_vwarehouse__warehouse_name', 'vwarehouse__warehouse_name', 'warehouse__warehouse_name','goods_name__goods_name', 'goods_id',]
    search_fields = ['order_id', 'goods_id']
    actions = [VASICheckAction, ]
    list_editable = ['memorandum']
    readonly_fields = ['va_stockin', 'order_id', 'order_category', 'ori_department','ori_vwarehouse', 'department', 'goods_id',
                       'goods_name', 'quantity', 'warehouse', 'vwarehouse', 'order_status', 'mistake_tag']
    form_layout = [
        Fieldset('主要信息',
                  'order_id', 'goods_name', 'order_category',  'quantity', 'ori_department', 'ori_vwarehouse', 'warehouse', 'vwarehouse', 'department'),
        Fieldset('一般信息',
                 'memorandum'),
        Fieldset(None,
                 'va_stockin', 'mistake_tag', 'creator', 'order_status', 'is_delete', 'dept_stock', **{"style": "display:None"}),
    ]

    def queryset(self):
        queryset = super(VASICheckAdmin, self).queryset()
        queryset = queryset.filter(is_delete=0, order_status=1)
        return queryset

    def has_add_permission(self):
        # 禁用添加按钮
        return False


# 处理本部门虚拟调拨入库单
class VASIHandleAction(BaseActionView):
    action_name = "handle_va_si"
    description = "提交选中的分配单"
    model_perm = 'change'
    icon = "fa fa-check-square-o"

    modify_models_batch = True

    @filter_hook
    def do_action(self, queryset):
        if not self.has_change_permission():
            raise PermissionDenied
        n = queryset.count()
        if n:
            if self.modify_models_batch:
                self.log('change',
                         '批量审核了 %(count)d %(items)s.' % {"count": n, "items": model_ngettext(self.opts, n)})
                queryset.update(order_status=3)
            else:
                for obj in queryset:
                    self.log('change', '', obj)

                obj.order_status = 2
                obj.mistake_tag = 0
                obj.save()
            self.message_user("成功提交 %(count)d %(items)s." % {"count": n, "items": model_ngettext(self.opts, n)},
                              'success')
        return None


# 本部门虚拟入库列表
class VASIMineAdmin(object):
    list_display = ['order_id', 'order_status', 'mistake_tag', 'order_category', 'ori_department',
                    'ori_vwarehouse', 'vwarehouse', 'warehouse', 'goods_name', 'goods_id', 'quantity', 'department',
                    'memorandum', ]
    list_filter = ['order_status', 'mistake_tag', 'order_category', 'department__name', 'ori_department__name', 'ori_vwarehouse__warehouse_name', 'vwarehouse__warehouse_name', 'warehouse__warehouse_name','goods_name__goods_name', 'goods_id',]
    search_fields = ['order_id', 'goods_id']
    actions = [VASIHandleAction, ]
    list_editable = ['memorandum']
    readonly_fields = ['va_stockin', 'order_id', 'order_category', 'ori_department','ori_vwarehouse', 'department', 'goods_id',
                       'goods_name', 'quantity', 'warehouse', 'vwarehouse', 'order_status', 'mistake_tag']
    form_layout = [
        Fieldset('主要信息',
                  'order_id', 'goods_name', 'order_category',  'quantity', 'ori_department', 'ori_vwarehouse', 'warehouse', 'vwarehouse', 'department'),
        Fieldset('一般信息',
                 'memorandum'),
        Fieldset(None,
                 'va_stockin', 'mistake_tag', 'creator', 'order_status', 'is_delete', 'dept_stock', **{"style": "display:None"}),
    ]

    def queryset(self):
        queryset = super(VASIMineAdmin, self).queryset()
        queryset = queryset.filter(is_delete=0, order_status=2, department=self.request.user.department)
        return queryset

    def has_add_permission(self):
        # 禁用添加按钮
        return False


class VAllotSIInfoAdmin(object):
    list_display = ['order_id', 'order_status', 'mistake_tag', 'order_category', 'ori_department',
                    'ori_vwarehouse', 'vwarehouse', 'warehouse', 'goods_name', 'goods_id', 'quantity', 'department',
                    'memorandum', ]
    list_filter = ['order_status', 'mistake_tag', 'order_category', 'department__name', 'ori_department__name', 'ori_vwarehouse__warehouse_name', 'vwarehouse__warehouse_name', 'warehouse__warehouse_name','goods_name__goods_name', 'goods_id',]
    search_fields = ['order_id', 'goods_id']
    actions = [VASICheckAction, ]
    readonly_fields = ['va_stockin', 'order_id', 'order_category', 'ori_department','ori_vwarehouse', 'department', 'goods_id',
                       'goods_name', 'quantity', 'warehouse', 'vwarehouse', 'order_status', 'mistake_tag']
    form_layout = [
        Fieldset('主要信息',
                  'order_id', 'goods_name', 'order_category',  'quantity', 'ori_department', 'ori_vwarehouse', 'warehouse', 'vwarehouse', 'department'),
        Fieldset('一般信息',
                 'memorandum'),
        Fieldset(None,
                 'va_stockin', 'mistake_tag', 'creator', 'order_status', 'is_delete', 'dept_stock', **{"style": "display:None"}),
    ]

    def queryset(self):
        queryset = super(VAllotSIInfoAdmin, self).queryset()
        queryset = queryset.filter(is_delete=0, order_status=3)
        return queryset

    def has_add_permission(self):
        # 禁用添加按钮
        return False


xadmin.site.register(VASOCheck, VASOCheckAdmin)
xadmin.site.register(VASOHandle, VASOHandleAdmin)
xadmin.site.register(VAllotSOInfo, VAllotSOInfoAdmin)
xadmin.site.register(VASICheck, VASICheckAdmin)
xadmin.site.register(VASIMine, VASIMineAdmin)
xadmin.site.register(VAllotSIInfo, VAllotSIInfoAdmin)



