# -*- coding: utf-8 -*-
# @Time    : 2019/11/28 21:49
# @Author  : Hann
# @Site    : 
# @File    : adminx.py
# @Software: PyCharm


import xadmin

from xadmin.plugins.actions import BaseActionView
from xadmin.views.base import filter_hook
from xadmin.util import model_ngettext
from xadmin.layout import Fieldset

from .models import OriStockInPending, OriStockInInfo, StockInInfo

ACTION_CHECKBOX_NAME = '_selected_action'


class OriStockInPendingAdmin(object):
    pass


class OriStockInInfoAdmin(object):
    pass


class StockInInfoAdmin(object):
    pass


xadmin.site.register(OriStockInPending, OriStockInPendingAdmin)
xadmin.site.register(OriStockInInfo, OriStockInInfoAdmin)
xadmin.site.register(StockInInfo, StockInInfoAdmin)

