# -*- coding: utf-8 -*-
# @Time    : 2019/12/3 8:56
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

from .models import DistributionInfo, Undistribution
from apps.wms.stock.models import DeptStockInfo, StockInfo


ACTION_CHECKBOX_NAME = '_selected_action'


# 递交预分配单
class OriDOAction(BaseActionView):
    action_name = "submit_sti_ori"
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
                    if obj.warehouse.undistributed >= obj.quantity:
                        repeat_stock = DeptStockInfo.objects.filter(goods_name=obj.goods_name, warehouse=obj.warehouse.warehouse, vwarehouse=obj.vwarehouse)
                        if repeat_stock:
                            dp_stock = repeat_stock[0]
                            dp_stock.quantity += obj.quantity
                            dp_stock.save()
                        else:
                            dp_stock = DeptStockInfo()
                            attrs = ['goods_name', 'vwarehouse', 'quantity']
                            for attr in attrs:
                                value = getattr(obj, attr, None)
                                setattr(dp_stock, attr, value)
                            dp_stock.warehouse = obj.warehouse.warehouse
                            dp_stock.goods_id = obj.goods_name.goods_id
                            dp_stock.creator = self.request.user.username
                            dp_stock.save()
                        stock_order = StockInfo.objects.filter(id=obj.warehouse.id)[0]
                        stock_order.undistributed = stock_order.undistributed - obj.quantity
                        stock_order.save()

                    else:
                        self.message_user("%s 可分配库存不足，无法分配" % obj.distribution_order_id, "error")
                        n -= 1
                        obj.error_tag = 1
                        obj.save()
                        continue
                    obj.order_status = 2
                    obj.save()
                    # 设置入库单的入库数量。
                    self.message_user("%s 递交完毕" % obj.distribution_order_id, "info")

            self.message_user("成功提交 %(count)d %(items)s." % {"count": n, "items": model_ngettext(self.opts, n)},
                              'success')

        return None


class DistributionInfoAdmin(object):
    list_display = ['order_status', 'distribution_order_id', 'warehouse', 'department', 'goods_name', 'quantity',
                    'memorandum', 'vwarehouse', 'creator', 'create_time', 'update_time']
    list_filter = ['creator', 'order_status', 'warehouse__warehouse__warehouse_name', 'department__name',
                   'goods_name__goods_name', 'quantity', 'memorandum','vwarehouse__warehouse_name',
                   'create_time', 'update_time']

    def has_add_permission(self):
        # 禁用添加按钮
        return False



class UndistributionAdmin(object):
    # 特别注意一下，就是源仓库是存货属性，之前命名搞懵逼了，结果代码写了多一半就不改了，自己备注下，将来不至于懵逼
    list_display = ['order_status','error_tag', 'distribution_order_id', 'warehouse', 'department', 'goods_name', 'quantity',
                    'undistribution_q', 'available_q', 'memorandum', 'vwarehouse', 'creator', 'create_time', 'update_time']
    list_filter = ['creator', 'order_status', 'warehouse__warehouse__warehouse_name', 'department__name',
                   'goods_name__goods_name', 'quantity', 'memorandum','vwarehouse__warehouse_name',
                   'create_time', 'update_time']
    list_editable =['quantity']
    actions = [OriDOAction, ]

    form_layout = [
        Fieldset('必填信息',
                 'goods_name', "warehouse", "quantity", "department", 'goods_name', 'quantity', 'vwarehouse'),
        Fieldset('选填信息',
                 'memorandum'),
        Fieldset(None,
                 'creator', 'order_status', 'is_delete', 'distribution_order_id','error_tag', **{"style": "display:None"}),
    ]

    def queryset(self):
        queryset = super(UndistributionAdmin, self).queryset()
        queryset = queryset.filter(is_delete=0, order_status=1)
        return queryset

    def save_models(self):
        obj = self.new_obj
        request = self.request
        obj.creator = request.user.username
        obj.save()
        if not obj.distribution_order_id:
            prefix = "DO"
            serial_number = str(datetime.datetime.now())
            serial_number = int(serial_number.replace("-", "").replace(" ", "").replace(":", "").replace(".", "")) + i
            distribution_order_id = prefix + str(serial_number) + "A"
            obj.distribution_order_id = distribution_order_id
            obj.save()

        super().save_models()



# xadmin.site.register(Undistribution, UndistributionAdmin)
# xadmin.site.register(DistributionInfo, DistributionInfoAdmin)
