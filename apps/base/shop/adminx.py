# -*- coding: utf-8 -*-
# @Time    : 2019/11/20 21:53
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
from xadmin.plugins.actions import BaseActionView
from xadmin.views.base import filter_hook
from xadmin.util import model_ngettext
from xadmin.layout import Fieldset

from .models import PlatformInfo, ShopInfo

ACTION_CHECKBOX_NAME = '_selected_action'


class PlatformInfoAdmin(object):
    list_display = ['p_name', 'order_status', 'creator', 'create_time']
    search_fields = ['p_name']
    form_layout = [
        Fieldset('必填信息',
                 'p_name', 'order_status'),
        Fieldset(None,
                 'creator', 'is_delete', **{"style": "display:None"}),
    ]

    def save_models(self):
        obj = self.new_obj
        request = self.request
        obj.creator = request.user.username
        obj.save()
        super(PlatformInfoAdmin, self).save_models()


class ShopInfoAdmin(object):
    list_display = ['shop_id','shop_name', 'department', 'company', 'cs_name', 'platform', 'create_time', 'creator']
    list_filter = ['shop_name']
    search_fields = ['name']
    form_layout = [
        Fieldset('必填信息',
                 'shop_name', 'shop_id', 'cs_name', 'department', 'platform', 'order_status'),
        Fieldset(None,
                 'creator', 'is_delete', **{"style": "display:None"}),
    ]
    actions = []

    def save_models(self):
        obj = self.new_obj
        request = self.request
        obj.creator = request.user.username
        obj.save()
        super(ShopInfoAdmin, self).save_models()


xadmin.site.register(PlatformInfo, PlatformInfoAdmin)
xadmin.site.register(ShopInfo, ShopInfoAdmin)

