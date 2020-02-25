# coding: utf-8
# @Time : 2020/2/23 1:34 PM
# @Author: Hann
# @File: adminx.py

import re
import pandas as pd
import datetime

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

from .models import CovertSI, CovertSIUnhandle, CovertSO, CovertSOUnhandle
from apps.base.department.models import DepartmentInfo
from apps.base.warehouse.models import WarehouseVirtual, WarehouseInfo
from apps.base.company.models import CompanyInfo
from apps.base.goods.models import GoodsInfo


class CovertSIUnhandleAdmin(object):
    list_display = ['order_id', 'mistake_tag', 'order_status', 'order_category', 'origin_order_category', 'supplier',
                    'department', 'goods_id','goods_name', 'quantity_receivable', 'quantity_received', 'payee',
                    'warehouse', 'origin_order_id',  'ori_creator',  'stockin_date', 'purchaser',
                    'batch_number',  'expiry_date', 'produce_date', 'memorandum',
                    'price', 'quantity_linking']
    list_filter = ['order_category', 'department__name', 'create_date', 'supplier__company_name', 'stockin_date',
                   'goods_name__goods_name', 'warehouse__warehouse_name']
    search_fields = ['order_id']


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
                    'quantity', 'warehouse', 'price', 'amount', 'package_size', 'buyer', 'address']

    list_filter = ['mistake_tag', 'order_status', 'order_category', 'department__name', 'goods_name__goods_name',
                   'warehouse__warehouse_name', 'goods_id', 'sale_organization',  'date']

    search_fields = ['order_id', 'origin_order_id']


class CovertSOAdmin(object):
    list_display = ['order_id', 'customer', 'order_category', 'origin_order_category', 'origin_order_id',
                    'sale_organization', 'department', 'memorandum', 'ori_creator', 'date', 'goods_id', 'goods_name',
                    'quantity', 'warehouse', 'price', 'amount', 'package_size', 'buyer', 'address']

    list_filter = ['mistake_tag', 'order_status', 'order_category', 'department__name', 'goods_name__goods_name',
                   'warehouse__warehouse_name', 'goods_id', 'sale_organization',  'date']

    search_fields = ['order_id', 'origin_order_id']


xadmin.site.register(CovertSIUnhandle, CovertSIUnhandleAdmin)
xadmin.site.register(CovertSI, CovertSIAdmin)
xadmin.site.register(CovertSOUnhandle, CovertSOUnhandleAdmin)
xadmin.site.register(CovertSO, CovertSOAdmin)








ACTION_CHECKBOX_NAME = '_selected_action'