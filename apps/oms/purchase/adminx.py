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

from .models import PurchaseInfo, PurchasePending
from apps.base.goods.models import GoodsInfo
from apps.base.company.models import ManuInfo


ACTION_CHECKBOX_NAME = '_selected_action'


class PurchaseInfoAdmin(object):
    list_display = ['purchase_order_id','purchase_time','status','goods_name','goods_id','goods_unit','quantity','complete_quantity','price','delivery_date','supplier']
    list_filter = ['purchase_time','supplier','puchaser','quantity','delivery_date','goods_name',]


class PurchasePendingAdmin(object):
    pass


xadmin.site.register(PurchaseInfo, PurchaseInfoAdmin)
xadmin.site.register(PurchasePending, PurchasePendingAdmin)


