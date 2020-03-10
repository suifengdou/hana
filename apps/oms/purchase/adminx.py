# -*- coding: utf-8 -*-
# @Time    : 2019/11/28 20:56
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

from .models import PurchaseInfo, PurchaseTrack
from apps.base.goods.models import GoodsInfo
from apps.base.company.models import ManuInfo


ACTION_CHECKBOX_NAME = '_selected_action'


class PurchaseInfoAdmin(object):
    list_display = ['purchase_order_id', 'order_id', 'purchase_time', 'order_status', 'goods_name', 'goods_id', 'quantity',
                    'complete_quantity', 'price', 'delivery_date', 'supplier']

    list_filter = ['purchase_time',]


class PurchaseTrackAdmin(object):
    list_display = ['purchase_order_id', 'order_id', 'purchase_time', 'order_status', 'goods_name', 'goods_id', 'quantity',
                    'complete_quantity', 'price', 'delivery_date', 'supplier']
    list_filter = ['mistake_tag', 'purchase_time',]


# xadmin.site.register(PurchaseTrack, PurchaseTrackAdmin)
# xadmin.site.register(PurchaseInfo, PurchaseInfoAdmin)


