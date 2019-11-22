# -*- coding: utf-8 -*-
# @Time    : 2019/11/19 20:14
# @Author  : Hann
# @Site    : 
# @File    : adminx.py
# @Software: PyCharm

from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.db import router
from django.utils.encoding import force_text
from django.template.response import TemplateResponse
from django.contrib.admin.utils import get_deleted_objects


import xadmin
from .models import BarCodeToGoods, SeriesToManu
from xadmin.plugins.actions import BaseActionView
from xadmin.views.base import filter_hook
from xadmin.util import model_ngettext
from xadmin.layout import Fieldset

ACTION_CHECKBOX_NAME = '_selected_action'


class BarCodeToGoodsAdmin(object):
    list_display = ['order_status', 'barcode', 'goods', 'create_time', 'creator']
    search_fields = ['goods__goods_name', 'barcode__barcode']
    form_layout = [
        Fieldset('必填信息',
                 'barcode', 'goods', 'order_status'),
        Fieldset(None,
                 'creator', 'is_delete', **{"style": "display:None"}),
    ]
    actions = []

    def save_models(self):
        obj = self.new_obj
        request = self.request
        obj.creator = request.user.username
        obj.save()
        super().save_models()


class SeriesToManuAdmin(object):
    list_display = ['order_status', 'manufactory', 'series', 'create_time', 'creator']
    search_fields = ['series__s_name', 'manufactory__company_name']
    form_layout = [
        Fieldset('必填信息',
                 'series', 'manufactory', 'order_status'),
        Fieldset(None,
                 'creator', 'is_delete', **{"style": "display:None"}),
    ]
    actions = []

    def save_models(self):
        obj = self.new_obj
        request = self.request
        obj.creator = request.user.username
        obj.save()
        super().save_models()


xadmin.site.register(BarCodeToGoods, BarCodeToGoodsAdmin)
xadmin.site.register(SeriesToManu, SeriesToManuAdmin)
