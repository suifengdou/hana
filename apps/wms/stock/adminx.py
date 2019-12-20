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


from .models import StockInfo, DeptStockInfo


class StockInfoAdmin(object):
    list_display = ['goods_name', 'goods_id', 'warehouse', 'quantity', 'undistributed', 'memorandum', 'order_status']


class DeptStockInfoAdmin(object):
    list_display = ['goods_name', 'goods_id', 'warehouse', 'vwarehouse', 'quantity', 'memorandum', 'order_status']


xadmin.site.register(StockInfo, StockInfoAdmin)
xadmin.site.register(DeptStockInfo, DeptStockInfoAdmin)