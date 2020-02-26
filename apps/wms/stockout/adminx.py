# coding: utf-8
# @Time : 2020/1/29 9:16 AM
# @Author: Hann
# @File: adminx.py


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

from .models import OriStockOut, OriStockOutUnhandle, StockOut, StockOutUnhandle


class OriStockOutUnhandleAdmin(object):
    list_display = []


class OriStockOutAdmin(object):
    list_display = []


class StockOutUnhandleAdmin(object):
    list_display = []


class StockOutAdmin(object):
    list_display = []


# xadmin.site.register(OriStockOutUnhandle, OriStockOutUnhandleAdmin)
# xadmin.site.register(OriStockOut, OriStockOutAdmin)
# xadmin.site.register(StockOutUnhandle, StockOutUnhandleAdmin)
# xadmin.site.register(StockOut, StockOutAdmin)