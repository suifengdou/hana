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

from .models import CovertSI, CovertSIUnhandle, CovertSO, CovertSOUnhandle, StockoutList, CovertLOUnhandle, CovertLoss
from apps.base.warehouse.models import WarehouseVirtual, WarehouseInfo
from apps.base.relationship.models import DeptToVW, DeptToW
from apps.wms.stock.models import StockInfo, DeptStockInfo
from apps.base.department.models import  CentreInfo

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


# 递交入库调整单
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
                    centre = obj.department.centre
                    _q_vwarehouse = DeptToVW.objects.filter(centre=centre)
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
                        if check_quantity is None:
                            check_quantity = 0
                        check_quantity = check_quantity + obj.quantity_received
                        if check_quantity != current_stock.quantity:
                            self.message_user("单号%s不要重复点递交，多线程递交会造成程序错乱" % obj.order_id, "error")
                            n -= 1
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
                            _q_stock_virtual = DeptStockInfo.objects.filter(centre=obj.department.centre,
                                                                            goods_name=obj.goods_name,
                                                                            warehouse=obj.warehouse,
                                                                            vwarehouse=vwarehouse)

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
                                stock_virtual.centre = obj.department.centre
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

                        stock_virtual.centre = obj.department.centre
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


# 修复虚拟仓保存失败入
class FixVWAction(BaseActionView):
        action_name = "fixvw_covert_si"
        description = "修复选中的订单"
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
                        centre = obj.department.centre
                        _q_vwarehouse = DeptToVW.objects.filter(centre=centre)
                        if _q_vwarehouse.exists():
                            vwarehouse = _q_vwarehouse[0].warehouse
                        else:
                            self.message_user("单号%s部门没有映射部门仓库，请设置对应仓库" % obj.order_id, "error")
                            n -= 1
                            obj.mistake_tag = 1
                            obj.save()
                            continue

                        if obj.mistake_tag == 4:
                            self.log('change', '', obj)

                            _q_stock_virtual = DeptStockInfo.objects.filter(centre=obj.department.centre,
                                                                            goods_name=obj.goods_name,
                                                                            warehouse=obj.warehouse,
                                                                            vwarehouse=vwarehouse)

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
                                stock_virtual.centre = obj.department.centre
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
                            obj.order_status = 2
                            obj.quantity_linking = obj.quantity_received
                            obj.mistake_tag = 0
                            obj.save()
                        else:
                            self.message_user("只有虚拟库存保存失败才可以修复", "error")
                            n -= 1
                            continue

                self.message_user("成功修复 %(count)d %(items)s." % {"count": n, "items": model_ngettext(self.opts, n)},
                                  'success')

            return None


# #####未审核入库调整单#####
class CovertSIUnhandleAdmin(object):
    list_display = ['order_id', 'mistake_tag', 'order_status', 'order_category', 'origin_order_category', 'supplier',
                    'department', 'goods_id','goods_name', 'quantity_receivable', 'quantity_received', 'payee',
                    'warehouse', 'origin_order_id',  'ori_creator',  'stockin_date', 'purchaser',
                    'batch_number',  'expiry_date', 'produce_date', 'memorandum', 'price', 'quantity_linking']
    list_filter = ['order_category', 'department__name', 'create_date', 'stockin_date',
                   'goods_name__goods_name', 'goods_id', 'warehouse__warehouse_name']
    search_fields = ['order_id']
    actions = [CovertSIAction, FixVWAction]

    def queryset(self):
        queryset = super(CovertSIUnhandleAdmin, self).queryset()
        queryset = queryset.filter(is_delete=0, order_status=1)
        return queryset

    def has_add_permission(self):
        # 禁用添加按钮
        return False


# 入库调整单
class CovertSIAdmin(object):
    list_display = ['order_id', 'mistake_tag', 'order_status', 'order_category', 'origin_order_category', 'supplier',
                    'department', 'goods_id','goods_name', 'quantity_receivable', 'quantity_received', 'payee',
                    'warehouse', 'origin_order_id',  'ori_creator',  'stockin_date', 'purchaser',
                    'batch_number',  'expiry_date', 'produce_date', 'memorandum', 'price', 'quantity_linking']
    list_filter = ['order_category', 'department__name', 'create_date', 'stockin_date',
                   'goods_name__goods_name', 'goods_id', 'warehouse__warehouse_name']
    search_fields = ['order_id']

    def has_add_permission(self):
        # 禁用添加按钮
        return False


# 递交出库调整单
class CovertSOAction(BaseActionView):
    action_name = "submit_so_ori"
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
                    _q_repeat_so = StockoutList.objects.filter(order_id=obj.order_id)
                    if _q_repeat_so.exists():
                        self.message_user("单号%s不要重复点递交，多线程递交会造成程序错乱" % obj.order_id, "error")
                        n -= 1
                        obj.mistake_tag = 1
                        obj.save()
                        continue
                    _q_stock_virtual = DeptStockInfo.objects.filter(centre=obj.department.centre,
                                                                    warehouse=obj.warehouse,
                                                                    goods_name=obj.goods_name)
                    if _q_stock_virtual.exists():
                        stock_virtual = _q_stock_virtual[0]
                        stock_virtual.quantity = stock_virtual.quantity - obj.quantity
                        if stock_virtual.quantity < 0:
                            self.message_user("单号%s部门存货不足" % obj.order_id, "error")
                            n -= 1
                            obj.mistake_tag = 2
                            obj.save()
                            continue
                        stocklist = StockoutList()
                        stocklist.order_id = obj.order_id
                        stocklist.creator = self.request.user.username
                        try:
                            stocklist.save()
                        except Exception as e:
                            self.message_user("单号%s保存历史记录失败，错误：%s" % (obj.order_id, e), "error")
                            n -= 1
                            obj.mistake_tag = 3
                            obj.save()
                            continue
                        try:
                            stock_virtual.save()
                        except Exception as e:
                            self.message_user("单号%s保存部门仓失败，错误：%s" % (obj.order_id, e), "error")
                            n -= 1
                            obj.mistake_tag = 4
                            obj.save()
                            continue
                        stock = StockInfo.objects.filter(warehouse=obj.warehouse, goods_name=obj.goods_name)[0]
                        if obj.department.centre.category == 1:
                            stock.undistributed = stock.undistributed - obj.quantity
                            stock.quantity = stock.quantity - obj.quantity
                        else:
                            stock.quantity = stock.quantity - obj.quantity
                        try:
                            stock.save()
                        except Exception as e:
                            self.message_user("单号%s保存实仓失败，错误：%s" % (obj.order_id, e), "error")
                            n -= 1
                            obj.mistake_tag = 5
                            obj.save()
                            continue
                        convert_si = CovertSIUnhandle.objects.filter(goods_name=obj.goods_name,
                                                                     warehouse=obj.warehouse).order_by('stockin_date')

                        minuend = obj.quantity
                        for c_si in convert_si:
                            if minuend > c_si.quantity_linking:
                                minuend = minuend - c_si.quantity_linking
                                c_si.quantity_linking = 0
                                stocklist.si_order_id = '{0}+{1}'.format(str(stocklist.si_order_id), str(c_si.order_id))
                                stocklist.si_order_id = stocklist.si_order_id[:300]
                                stocklist.save()
                                c_si.save()
                            else:
                                c_si.quantity_linking = c_si.quantity_linking - minuend
                                stocklist.si_order_id = '{0}+{1}'.format(str(stocklist.si_order_id), str(c_si.order_id))
                                stocklist.si_order_id = stocklist.si_order_id[:300]
                                stocklist.save()
                                c_si.save()
                                break
                    else:
                        self.message_user("单号%s部门没有此货品" % obj.order_id, "error")
                        n -= 1
                        obj.mistake_tag = 7
                        obj.save()
                        continue

                    obj.order_status = 2
                    obj.mistake_tag = 0
                    obj.save()

            self.message_user("成功提交 %(count)d %(items)s." % {"count": n, "items": model_ngettext(self.opts, n)},
                              'success')

        return None


# #####未审核出库调整单#####
class CovertSOUnhandleAdmin(object):
    list_display = ['order_id', 'mistake_tag', 'order_status', 'customer', 'order_category', 'origin_order_category', 'origin_order_id',
                    'sale_organization', 'department', 'memorandum', 'ori_creator', 'date', 'goods_id', 'goods_name',
                    'quantity', 'warehouse', 'price', 'amount', 'buyer', 'address']

    list_filter = ['mistake_tag', 'order_status', 'order_category', 'department__name', 'goods_name__goods_name',
                   'warehouse__warehouse_name', 'goods_id', 'sale_organization',  'date']
    actions = [CovertSOAction, ]
    search_fields = ['order_id', 'origin_order_id']

    def queryset(self):
        queryset = super(CovertSOUnhandleAdmin, self).queryset()
        queryset = queryset.filter(is_delete=0, order_status=1)
        return queryset

    def has_add_permission(self):
        # 禁用添加按钮
        return False


# 出库调整单查询。
class CovertSOAdmin(object):
    list_display = ['order_id', 'customer', 'order_category', 'origin_order_category', 'origin_order_id',
                    'sale_organization', 'department', 'memorandum', 'ori_creator', 'date', 'goods_id', 'goods_name',
                    'quantity', 'warehouse', 'price', 'amount', 'buyer', 'address']

    list_filter = ['mistake_tag', 'order_status', 'order_category', 'department__name', 'goods_name__goods_name',
                   'warehouse__warehouse_name', 'goods_id', 'sale_organization',  'date']

    search_fields = ['order_id', 'origin_order_id']

    def has_add_permission(self):
        # 禁用添加按钮
        return False


# 出库调整单已出库记录列表
class StockoutListAdmin(object):
    list_display = ['order_id', 'order_status', 'si_order_id', ]
    list_filter = ['order_id', 'order_status']
    search_fields = ['order_id']
    readonly_fields = ['order_id', 'order_status', 'si_order_id',]


# 盘点调整单的快捷部门选择。
class LOSetDeptAction(BaseActionView):
    action_name = "submit_set_department"
    description = "预处理选中的订单"
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
                des_department = CentreInfo.objects.filter(name='物流部')[0]
                for obj in queryset:
                    self.log('change', '', obj)
                    _q_department = DeptToW.objects.filter(warehouse=obj.warehouse)
                    if _q_department.exists():
                        obj.des_department = _q_department[0].centre
                        obj.order_category = obj.des_department.category
                    else:
                        obj.des_department = des_department
                        obj.order_category = obj.des_department.category
                    obj.save()
            self.message_user("成功提交 %(count)d %(items)s." % {"count": n, "items": model_ngettext(self.opts, n)},
                              'success')
        return None


# 盘点调整单的批量部门修改。
class LOSetFirstAction(BaseActionView):
    action_name = "submit_set_first"
    description = "修改为第一个单据的目的部门"
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
                des_department = CentreInfo.objects.filter(name='物流部')[0]
                i = 0
                for obj in queryset:
                    self.log('change', '', obj)
                    if i == 0:
                        des_department = obj.des_department
                        obj.order_category = obj.des_department.category
                        i += 1
                        continue
                    else:
                        obj.des_department = des_department
                        obj.order_category = obj.des_department.category
                        i += 1
                    obj.save()
            self.message_user("成功提交 %(count)d %(items)s." % {"count": n, "items": model_ngettext(self.opts, n)},
                              'success')
        return None


# 递交盘亏调整单
class CovertLOAction(BaseActionView):
    action_name = "submit_loss_ori"
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
                    if not obj.des_department:
                        self.message_user("单号%s没有指定目的部门，不允许递交" % obj.order_id, "error")
                        n -= 1
                        obj.mistake_tag = 1
                        obj.save()
                        continue
                    _q_repeat_so = StockoutList.objects.filter(order_id=obj.order_id)
                    if _q_repeat_so.exists():
                        self.message_user("单号%s不要重复点递交，多线程递交会造成程序错乱" % obj.order_id, "error")
                        n -= 1
                        obj.mistake_tag = 1
                        obj.save()
                        continue
                    _q_stock_virtual = DeptStockInfo.objects.filter(department=obj.des_department, warehouse=obj.warehouse, goods_name=obj.goods_name)
                    if _q_stock_virtual.exists():
                        stock_virtual = _q_stock_virtual[0]
                        stock_virtual.quantity = stock_virtual.quantity - obj.quantity
                        if stock_virtual.quantity < 0:
                            self.message_user("单号%s部门存货不足" % obj.order_id, "error")
                            n -= 1
                            obj.mistake_tag = 2
                            obj.save()
                            continue
                        stocklist = StockoutList()
                        stocklist.order_id = obj.order_id
                        stocklist.creator = self.request.user.username
                        try:
                            stocklist.save()
                        except Exception as e:
                            self.message_user("单号%s保存历史记录失败，错误：%s" % (obj.order_id, e), "error")
                            n -= 1
                            obj.mistake_tag = 3
                            obj.save()
                            continue
                        try:
                            stock_virtual.save()
                        except Exception as e:
                            self.message_user("单号%s保存部门仓失败，错误：%s" % (obj.order_id, e), "error")
                            n -= 1
                            obj.mistake_tag = 4
                            obj.save()
                            continue
                        stock = StockInfo.objects.filter(warehouse=obj.warehouse, goods_name=obj.goods_name)[0]
                        if obj.des_department.category == 1:
                            stock.undistributed = stock.undistributed - obj.quantity
                            stock.quantity = stock.quantity - obj.quantity
                        else:
                            stock.quantity = stock.quantity - obj.quantity
                        try:
                            stock.save()
                        except Exception as e:
                            self.message_user("单号%s保存实仓失败，错误：%s" % (obj.order_id, e), "error")
                            n -= 1
                            obj.mistake_tag = 5
                            obj.save()
                            continue
                        convert_si = CovertSIUnhandle.objects.filter(goods_name=obj.goods_name,
                                                                     warehouse=obj.warehouse).order_by('stockin_date')

                        minuend = obj.quantity
                        for c_si in convert_si:
                            if minuend > c_si.quantity_linking:
                                minuend = minuend - c_si.quantity_linking
                                c_si.quantity_linking = 0
                                stocklist.si_order_id = str(c_si.order_id)
                                stocklist.save()
                                c_si.save()
                            else:
                                c_si.quantity_linking = c_si.quantity_linking - minuend
                                stocklist.si_order_id = '{0}+{1}'.format(str(stocklist.si_order_id), str(c_si.order_id))
                                stocklist.si_order_id = stocklist.si_order_id[:300]
                                stocklist.save()
                                c_si.save()
                                break
                    else:
                        self.message_user("单号%s部门没有此货品" % obj.order_id, "error")
                        n -= 1
                        obj.mistake_tag = 7
                        obj.save()
                        continue

                    obj.order_status = 2
                    obj.mistake_tag = 0
                    obj.save()

            self.message_user("成功提交 %(count)d %(items)s." % {"count": n, "items": model_ngettext(self.opts, n)},
                              'success')

        return None


class CovertLOUnhandleAdmin(object):
    list_display = ['order_id', 'order_status', 'mistake_tag', 'customer', 'origin_order_category', 'origin_order_id',
                    'department', 'des_department', 'ori_creator', 'date', 'goods_id',
                    'goods_name', 'quantity', 'warehouse', 'memorandum']
    list_filter = ['order_status', 'mistake_tag', 'des_department__name','date', 'goods_id', 'goods_name__goods_name', 'quantity', 'warehouse__warehouse_name', ]
    search_fields = ['order_id', 'goods_id', 'origin_order_id',]
    list_editable = ['des_department']
    actions = [LOSetDeptAction, LOSetFirstAction, CovertLOAction]

    def queryset(self):
        queryset = super(CovertLOUnhandleAdmin, self).queryset()
        queryset = queryset.filter(is_delete=0, order_status=1)
        return queryset


class CovertLossAdmin(object):
    list_display = ['order_id', 'order_status', 'mistake_tag', 'customer', 'origin_order_category', 'origin_order_id',
                    'department', 'des_department', 'ori_creator', 'date', 'goods_id',
                    'goods_name', 'quantity', 'warehouse', 'memorandum']


xadmin.site.register(CovertSIUnhandle, CovertSIUnhandleAdmin)
xadmin.site.register(CovertSI, CovertSIAdmin)
xadmin.site.register(CovertSOUnhandle, CovertSOUnhandleAdmin)
xadmin.site.register(CovertSO, CovertSOAdmin)
xadmin.site.register(StockoutList, StockoutListAdmin)
xadmin.site.register(CovertLOUnhandle, CovertLOUnhandleAdmin)
xadmin.site.register(CovertLoss, CovertLossAdmin)


