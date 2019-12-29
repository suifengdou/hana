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

from .models import VirtualAllot, VAPending, VACheck, VAProcess
from apps.wms.stock.models import DeptStockInfo

ACTION_CHECKBOX_NAME = '_selected_action'


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
                    if obj.vwarehouse_ori.quantity >= obj.quantity:
                        obj.order_status = 2
                        obj.save()
                        self.message_user("%s 递交完毕" % obj.allot_order_id, "info")
                    else:
                        self.message_user("%s 源仓库存货不足" % obj.allot_order_id, "error")
                        obj.error_tag = 1
                        obj.save()

            self.message_user("成功提交 %(count)d %(items)s." % {"count": n, "items": model_ngettext(self.opts, n)},
                              'success')

        return None


# 审核虚拟调拨单
class AOCheckAction(BaseActionView):
    action_name = "check_oa"
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
                    if obj.vwarehouse_ori.quantity >= obj.quantity:
                        obj.order_status = 3
                        obj.save()
                        self.message_user("%s 递交完毕" % obj.allot_order_id, "info")
                    else:
                        self.message_user("%s 没货啦，别浪" % obj.allot_order_id, "error")
                        obj.error_tag = 1
                        obj.save()

            self.message_user("成功提交 %(count)d %(items)s." % {"count": n, "items": model_ngettext(self.opts, n)},
                              'success')
        return None


# 执行虚拟调拨单
class AOProcessAction(BaseActionView):
    action_name = "process_oa"
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
                    if obj.vwarehouse_ori.quantity >= obj.quantity:
                        allot_des = DeptStockInfo.objects.filter(warehouse=obj.vwarehouse_ori.warehouse, vwarehouse=obj.vwarehouse_des, goods_name=obj.goods_name)
                        if allot_des:
                            allot_des = allot_des[0]
                            allot_des.quantity = allot_des.quantity + obj.quantity
                            allot_des.save()
                        else:
                            allot_order = DeptStockInfo()
                            allot_order.goods_name = obj.goods_name
                            allot_order.goods_id = obj.goods_id
                            allot_order.warehouse = obj.vwarehouse_ori.warehouse
                            allot_order.vwarehouse = obj.vwarehouse_des
                            allot_order.quantity = obj.quantity
                            allot_order.save()
                        stock_order = DeptStockInfo.objects.filter(id=obj.vwarehouse_ori.id)[0]
                        stock_order.quantity = stock_order.quantity - obj.quantity
                        stock_order.save()
                        obj.order_status = 4
                        obj.save()
                        self.message_user("%s 递交完毕" % obj.allot_order_id, "info")
                    else:
                        self.message_user("%s 没货啦，浪不了了" % obj.allot_order_id, "error")
                        obj.error_tag = 1
                        obj.save()

            self.message_user("成功提交 %(count)d %(items)s." % {"count": n, "items": model_ngettext(self.opts, n)},
                              'success')

        return None


class VAPendingAdmin(object):
    # 特别注意一下，就是源仓库是存货属性，之前命名搞懵逼了，结果代码写了多一半就不改了，自己备注下，将来不至于懵逼
    list_display = ['allot_order_id', 'order_status', 'error_tag', 'vwarehouse_ori', 'vwarehouse_des', 'category', 'goods_name', 'goods_id', 'quantity', 'memorandum']
    list_filter = ['vwarehouse_ori__vwarehouse__warehouse_name', 'vwarehouse_des__warehouse_name', 'category', 'goods_name__goods_name', 'goods_id', 'quantity']
    list_editable = ['quantity']
    search_fields = ['goods_id']
    actions = [AOSubmitAction, ]

    form_layout = [
        Fieldset('主要信息',
                  'vwarehouse_ori', 'vwarehouse_des', 'category', 'goods_name',  'quantity'),
        Fieldset('一般信息',
                 'memorandum'),
        Fieldset(None,
                 'allot_order_id', 'error_tag', 'creator', 'order_status', 'is_delete', 'goods_id','department', **{"style": "display:None"}),
    ]

    def queryset(self):
        queryset = super(VAPendingAdmin, self).queryset()
        queryset = queryset.filter(is_delete=0, order_status=1)
        return queryset

    def has_add_permission(self):
        # 禁用添加按钮
        return False

    # def save_models(self):
    #     obj = self.new_obj
    #     request = self.request
    #     obj.creator = request.user.username
    #     obj.save()
    #     if not obj.allot_order_id:
    #         prefix = "AO"
    #         serial_number = str(datetime.datetime.now())
    #         serial_number = int(serial_number.replace("-", "").replace(" ", "").replace(":", "").replace(".", "")) + i
    #         allot_order_id = prefix + str(serial_number) + "A"
    #         obj.allot_order_id = allot_order_id
    #     obj.goods_id = obj.goods_name.goods_id
    #     department = DepartmentToWarehouse.objects.filter(warehouse=obj.vwarehouse_ori.vwarehouse)
    #     if department:
    #         obj.department = department[0].department
    #     try:
    #         obj.save()
    #     except Exception as e:
    #         self.message_user("保存出错：%s" % e, "error")
    #
    #     super().save_models()


class VACheckAdmin(object):
    list_display = ['allot_order_id', 'order_status', 'error_tag', 'vwarehouse_ori', 'vwarehouse_des', 'category', 'goods_name', 'goods_id', 'quantity', 'memorandum']
    list_filter = ['vwarehouse_ori__vwarehouse__warehouse_name', 'vwarehouse_des__warehouse_name', 'category', 'goods_name__goods_name', 'goods_id', 'quantity']
    list_editable = ['quantity', 'memorandum']
    readonly_fields = ['allot_order_id', 'order_status', 'error_tag', 'vwarehouse_ori', 'vwarehouse_des', 'category',
                       'goods_name', 'goods_id']
    search_fields = ['goods_id']
    actions = [AOCheckAction,]

    def queryset(self):
        if self.request.user.department:
            queryset = super(VACheckAdmin, self).queryset()
            queryset = queryset.filter(is_delete=0, order_status=2, department=self.request.user.department)
            return queryset
        else:
            self.message_user("请联系管理员设置部门。", "error")
            queryset = super(VACheckAdmin, self).queryset().filter(goods_id=0)
            return queryset

    def has_add_permission(self):
        # 禁用添加按钮
        return False


class VAProcessAdmin(object):
    list_display = ['allot_order_id', 'memorandum', 'order_status', 'error_tag', 'vwarehouse_ori', 'vwarehouse_des', 'category', 'goods_name', 'goods_id', 'quantity']
    list_filter = ['vwarehouse_ori__vwarehouse__warehouse_name', 'vwarehouse_des__warehouse_name', 'category', 'goods_name__goods_name', 'goods_id', 'quantity']
    list_editable = ['memorandum']
    readonly_fields = ['allot_order_id', 'order_status', 'error_tag', 'vwarehouse_ori', 'vwarehouse_des', 'category',
                       'goods_name', 'goods_id', 'quantity']
    search_fields = ['goods_id']
    actions = [AOProcessAction, ]

    def queryset(self):
        queryset = super(VAProcessAdmin, self).queryset()
        queryset = queryset.filter(is_delete=0, order_status=3)
        return queryset

    def has_add_permission(self):
        # 禁用添加按钮
        return False


class VirtualAllotAdmin(object):
    list_display = ['allot_order_id', 'order_status', 'error_tag', 'vwarehouse_ori', 'vwarehouse_des', 'category', 'goods_name', 'goods_id', 'quantity', 'memorandum']
    list_filter = ['vwarehouse_ori__vwarehouse__warehouse_name', 'vwarehouse_des__warehouse_name', 'category', 'goods_name__goods_name', 'goods_id', 'quantity']
    search_fields = ['goods_id']
    readonly_fields = ['allot_order_id', 'order_status', 'error_tag', 'vwarehouse_ori', 'vwarehouse_des', 'category', 'goods_name', 'goods_id', 'quantity', 'memorandum']

    def queryset(self):
        queryset = super(VirtualAllotAdmin, self).queryset()
        queryset = queryset.filter(is_delete=0, order_status=4)
        return queryset

    def has_add_permission(self):
        # 禁用添加按钮
        return False


xadmin.site.register(VAPending, VAPendingAdmin)
xadmin.site.register(VACheck, VACheckAdmin)
xadmin.site.register(VAProcess, VAProcessAdmin)
xadmin.site.register(VirtualAllot, VirtualAllotAdmin)