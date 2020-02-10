# -*- coding: utf-8 -*-
# @Time    : 2019/11/28 21:49
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

from .models import StockInInfo, StockInPending
from apps.base.company.models import ManuInfo
from apps.base.goods.models import GoodsInfo
from apps.base.warehouse.models import WarehouseGeneral
from apps.oms.purchase.models import PurchaseInfo
from apps.wms.stock.models import StockInfo, DeptStockInfo

ACTION_CHECKBOX_NAME = '_selected_action'


# 递交入库单
class SIAction(BaseActionView):
    action_name = "submit_sti_or"
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
                    if obj.quantity_received == obj.quantity_receivable:
                        current_quantity = obj.purchase_order_id.complete_quantity + obj.quantity_received
                        if obj.purchase_order_id.quantity >= current_quantity:
                            obj.purchase_order_id.complete_quantity = current_quantity
                            obj.purchase_order_id.save()
                        else:
                            obj.mistake_tag =2
                            n -= 1
                            obj.save()
                            continue
                    else:
                        obj.mistake_tag = 1
                        n -= 1
                        obj.save()
                        continue

                    is_exists = StockInfo.objects.filter(goods_name=obj.goods_name, warehouse=obj.warehouse)
                    if is_exists.exists():
                        stock_exists = is_exists[0]
                        stock_exists.quantity += obj.quantity_received
                        stock_exists.undistributed += obj.quantity_received
                        stock_exists.save()
                        obj.order_status = 2
                        obj.save()
                    else:
                        stock = StockInfo()
                        attrs = ['goods_name', 'goods_id', 'warehouse']
                        for att in attrs:
                            value = getattr(obj, att, None)
                            setattr(stock, att, value)
                        stock.undistributed = obj.quantity_received
                        stock.quantity = obj.quantity_received
                        stock.creator = self.request.user.username
                        try:
                            stock.save()
                        except Exception as e:
                            n -= 1
                            obj.mistake_tag = 3
                            obj.save()
                            continue
                        obj.order_status = 2
                        obj.save()

            self.message_user("成功提交 %(count)d %(items)s." % {"count": n, "items": model_ngettext(self.opts, n)},
                              'success')

        return None


class StockInPendingAdmin(object):
    list_display = ['order_category','mistake_tag','order_status', 'supplier', 'create_date', 'stockin_order_id', 'purchaser', 'goods_id',
                    'goods_name', 'goods_size', 'goods_unit', 'quantity_receivable', 'quantity_received',
                    'warehouse', 'origin_order_id', 'purchase_order_id', ]

    list_filter = ['mistake_tag', 'supplier', 'goods_id', 'goods_name', 'warehouse', 'origin_order_id', 'purchase_order_id', 'create_date', 'update_time', 'create_time','creator']
    search_fields = []
    actions = [SIAction]
    form_layout = [
        Fieldset('存货信息',
                 'goods_name', "warehouse", "quantity", 'goods_name', 'quantity'),
        Fieldset('选填信息',
                 'memorandum'),
        Fieldset(None,
                 'creator', 'order_status', 'is_delete', **{"style": "display:None"}),
    ]

    def queryset(self):
        queryset = super(StockInPendingAdmin, self).queryset()
        queryset = queryset.filter(is_delete=0, order_status=1)
        return queryset


class StockInInfoAdmin(object):
    list_display = ['order_category', 'supplier', 'create_date', 'stockin_order_id', 'purchaser', 'goods_id',
                    'goods_name', 'goods_size', 'goods_unit', 'quantity_receivable', 'quantity_received',
                    'warehouse', 'origin_order_id', 'purchase_order_id', ]
    list_filter = ['mistake_tag', 'supplier', 'goods_id', 'goods_name', 'warehouse', 'origin_order_id', 'purchase_order_id', 'create_date', 'update_time', 'create_time','creator']
    search_fields = []


xadmin.site.register(StockInPending, StockInPendingAdmin)
xadmin.site.register(StockInInfo, StockInInfoAdmin)

