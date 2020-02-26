# coding: utf-8
# @Time : 2020/2/23 1:34 PM
# @Author: Hann
# @File: adminx.py

import re
import pandas as pd
import datetime

from django.core.exceptions import PermissionDenied
from django.db.models import Q, Sum, Avg, Min, Max
from django.db import router
from django.utils.encoding import force_text
from django.template.response import TemplateResponse
from django.contrib.admin.utils import get_deleted_objects


import xadmin

from xadmin.plugins.actions import BaseActionView
from xadmin.views.base import filter_hook
from xadmin.util import model_ngettext
from xadmin.layout import Fieldset

from .models import CovertSI, CovertSIUnhandle, CovertSO, CovertSOUnhandle
from apps.base.warehouse.models import WarehouseVirtual, WarehouseInfo
from apps.base.relationship.models import DeptToVW
from apps.wms.stock.models import StockInfo, DeptStockInfo

ACTION_CHECKBOX_NAME = '_selected_action'


class RejectSelectedAction(BaseActionView):

    action_name = "reject_selected"
    description = '驳回选中的单据'

    delete_confirmation_template = None
    delete_selected_confirmation_template = None

    delete_models_batch = False

    model_perm = 'change'
    icon = 'fa fa-times'

    @filter_hook
    def reject_models(self, queryset):
        n = queryset.count()
        if n:
            for obj in queryset:
                if obj.order_status > 0:
                    obj.order_status -= 1
                    obj.save()
                    if obj.order_status == 0:
                        self.message_user("%s 取消成功" % obj.order_id, "success")
                    else:
                        self.message_user("%s 驳回上一级成功" % obj.order_id, "success")
                else:
                    n -= 1
                    self.message_user("%s 单据状态错误，请检查，驳回出错。" % obj.order_id, "error")
            self.message_user("成功驳回 %(count)d %(items)s." % {"count": n, "items": model_ngettext(self.opts, n)},
                              'success')
        return None

    @filter_hook
    def do_action(self, queryset):
        # Check that the user has delete permission for the actual model
        if not self.has_change_permission():
            raise PermissionDenied

        using = router.db_for_write(self.model)

        # Populate deletable_objects, a data structure of all related objects that
        # will also be deleted.
        deletable_objects, model_count, perms_needed, protected = get_deleted_objects(
            queryset, self.opts, self.user, self.admin_site, using)

        # The user has already confirmed the deletion.
        # Do the deletion and return a None to display the change list view again.
        if self.request.POST.get('post'):
            if not self.has_change_permission():
                raise PermissionDenied
            self.reject_models(queryset)
            # Return None to display the change list page again.
            return None

        if len(queryset) == 1:
            objects_name = force_text(self.opts.verbose_name)
        else:
            objects_name = force_text(self.opts.verbose_name_plural)
        perms_needed = []
        if perms_needed or protected:
            title = "Cannot reject %(name)s" % {"name": objects_name}
        else:
            title = "Are you sure?"

        context = self.get_context()
        context.update({
            "title": title,
            "objects_name": objects_name,
            "deletable_objects": [deletable_objects],
            'queryset': queryset,
            "perms_lacking": perms_needed,
            "protected": protected,
            "opts": self.opts,
            "app_label": self.app_label,
            'action_checkbox_name': ACTION_CHECKBOX_NAME,
        })

        # Display the confirmation page
        return TemplateResponse(self.request, self.delete_selected_confirmation_template or
                                self.get_template_list('views/model_reject_selected_confirm.html'), context)


# 递交原始采购入库单
class CovertSIAction(BaseActionView):
    action_name = "submit_covert_si"
    description = "提交选中的订单"
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
                    department = obj.department
                    _q_vwarehouse = DeptToVW.objects.filter(department=department)
                    if _q_vwarehouse.exists():
                        vwarehouse = _q_vwarehouse[0].warehouse
                    else:
                        self.message_user("单号%s部门没有映射部门仓库，请设置对应仓库" % obj.order_id, "error")
                        n -= 1
                        obj.mistake_tag = 1
                        obj.save()
                        continue

                    _q_stock = StockInfo.objects.filter(warehouse=obj.warehouse, goods_name=obj.goods_name)
                    if _q_stock.exists():
                        current_stock = _q_stock[0]
                        current_stock.quantity = obj.quantity_received + current_stock.quantity
                        check_quantity = CovertSI.objects.filter(order_status=2, warehouse=obj.warehouse,
                                                                 goods_name=obj.goods_name).aggregate(
                                                                Sum('quantity_linking'))['quantity_linking__sum']
                        check_quantity = check_quantity + obj.quantity_received
                        if check_quantity != current_stock.quantity:
                            self.message_user("单号%s不要重复点递交，多线程递交会造成程序错乱" % obj.order_id, "error")
                            n -= 1
                            obj.mistake_tag = 2
                            obj.save()
                            continue
                        else:
                            if obj.department.category == 1:
                                current_stock.undistributed = current_stock.undistributed + obj.quantity_received
                            try:
                                current_stock.save()
                            except Exception as e:
                                self.message_user("单号%s实仓实例保存失败, 错误：%s" % (obj.order_id, e), "error")
                                n -= 1
                                obj.mistake_tag = 3
                                obj.save()
                                continue
                            _q_stock_virtual = DeptStockInfo.objects.filter(goods_name=obj.goods_name, warehouse=obj.warehouse, vwarehouse=vwarehouse)
                            if _q_stock_virtual.exists():
                                stock_virtual = _q_stock_virtual[0]
                                stock_virtual.quantity = stock_virtual.quantity + obj.quantity_received
                                try:
                                    stock_virtual.save()
                                except Exception as e:
                                    self.message_user("单号%s部门仓实例保存失败, 错误：%s" % (obj.order_id, e), "error")
                                    n -= 1
                                    obj.mistake_tag = 4
                                    obj.save()
                                    continue
                            else:
                                stock_virtual = DeptStockInfo()
                                stock_virtual.goods_name = obj.goods_name
                                stock_virtual.goods_id = obj.goods_id
                                stock_virtual.warehouse = obj.warehouse
                                stock_virtual.vwarehouse = vwarehouse
                                stock_virtual.quantity = obj.quantity_received

                                try:
                                    stock_virtual.creator = self.request.user.username
                                    stock_virtual.save()
                                except Exception as e:
                                    self.message_user("单号%s部门仓实例保存失败, 错误：%s" % (obj.order_id, e), "error")
                                    n -= 1
                                    obj.mistake_tag = 4
                                    obj.save()
                                    continue
                    else:
                        stock = StockInfo()
                        stock_virtual = DeptStockInfo()

                        fields_list = ['goods_name', 'goods_id', 'warehouse']

                        for k in fields_list:
                            if hasattr(obj, k):
                                setattr(stock, k, getattr(obj, k))  # 更新对象属性对应键值
                        for k in fields_list:
                            if hasattr(obj, k):
                                setattr(stock_virtual, k, getattr(obj, k))  # 更新对象属性对应键值

                        stock.quantity = obj.quantity_received
                        if obj.department.category == 1:
                            stock.undistributed = obj.quantity_received
                        else:
                            stock.undistributed = 0

                        stock_virtual.vwarehouse = vwarehouse
                        stock_virtual.quantity = obj.quantity_received
                        try:

                            stock.creator = self.request.user.username
                            stock.save()
                        except Exception as e:
                            self.message_user("单号%s实仓实例保存失败, 错误：%s" % (obj.order_id, e), "error")
                            n -= 1
                            obj.mistake_tag = 3
                            obj.save()
                            continue
                        try:
                            stock_virtual.creator = self.request.user.username
                            stock_virtual.save()
                        except Exception as e:
                            self.message_user("单号%s部门仓实例保存失败, 错误：%s" % (obj.order_id, e), "error")
                            n -= 1
                            obj.mistake_tag = 4
                            obj.save()
                            continue

                    obj.order_status = 2
                    obj.quantity_linking = obj.quantity_received
                    obj.mistake_tag = 0
                    obj.save()

            self.message_user("成功提交 %(count)d %(items)s." % {"count": n, "items": model_ngettext(self.opts, n)},
                              'success')

        return None


class CovertSIUnhandleAdmin(object):
    list_display = ['order_id', 'mistake_tag', 'order_status', 'order_category', 'origin_order_category', 'supplier',
                    'department', 'goods_id','goods_name', 'quantity_receivable', 'quantity_received', 'payee',
                    'warehouse', 'origin_order_id',  'ori_creator',  'stockin_date', 'purchaser',
                    'batch_number',  'expiry_date', 'produce_date', 'memorandum',
                    'price', 'quantity_linking']
    list_filter = ['order_category', 'department__name', 'create_date', 'supplier__company_name', 'stockin_date',
                   'goods_name__goods_name', 'warehouse__warehouse_name']
    search_fields = ['order_id']
    actions = [CovertSIAction, ]


class CovertSIAdmin(object):
    list_display = ['order_id', 'mistake_tag', 'order_status', 'order_category', 'origin_order_category', 'supplier',
                    'department', 'goods_id','goods_name', 'quantity_receivable', 'quantity_received', 'payee',
                    'warehouse', 'origin_order_id',  'ori_creator',  'stockin_date', 'purchaser',
                    'batch_number',  'expiry_date', 'produce_date', 'memorandum',
                    'price', 'quantity_linking']
    list_filter = ['order_category', 'department__name', 'create_date', 'supplier__company_name', 'stockin_date',
                   'goods_name__goods_name', 'warehouse__warehouse_name']
    search_fields = ['order_id']


class CovertSOUnhandleAdmin(object):
    list_display = ['order_id', 'mistake_tag', 'order_status', 'customer', 'order_category', 'origin_order_category', 'origin_order_id',
                    'sale_organization', 'department', 'memorandum', 'ori_creator', 'date', 'goods_id', 'goods_name',
                    'quantity', 'warehouse', 'price', 'amount', 'buyer', 'address']

    list_filter = ['mistake_tag', 'order_status', 'order_category', 'department__name', 'goods_name__goods_name',
                   'warehouse__warehouse_name', 'goods_id', 'sale_organization',  'date']

    search_fields = ['order_id', 'origin_order_id']


class CovertSOAdmin(object):
    list_display = ['order_id', 'customer', 'order_category', 'origin_order_category', 'origin_order_id',
                    'sale_organization', 'department', 'memorandum', 'ori_creator', 'date', 'goods_id', 'goods_name',
                    'quantity', 'warehouse', 'price', 'amount', 'buyer', 'address']

    list_filter = ['mistake_tag', 'order_status', 'order_category', 'department__name', 'goods_name__goods_name',
                   'warehouse__warehouse_name', 'goods_id', 'sale_organization',  'date']

    search_fields = ['order_id', 'origin_order_id']


xadmin.site.register(CovertSIUnhandle, CovertSIUnhandleAdmin)
xadmin.site.register(CovertSI, CovertSIAdmin)
xadmin.site.register(CovertSOUnhandle, CovertSOUnhandleAdmin)
xadmin.site.register(CovertSO, CovertSOAdmin)








ACTION_CHECKBOX_NAME = '_selected_action'