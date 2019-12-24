# coding: utf-8
# @Time : 2019/11/24 10:12 PM
# @Author: Hann
# @File: adminx.py


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

from .models import WarehouseInfo, WarehouseGeneral, WarehouseManu, WarehouseVirtual

ACTION_CHECKBOX_NAME = '_selected_action'


class WarehouseInfoAdmin(object):
    list_display = ['warehouse_id', 'warehouse_name', 'city', 'category', 'order_status']
    list_filter = ['category', 'order_status']
    search_fields = ['warehouse_name']
    relfield_style = 'fk-ajax'
    # model_icon = 'fa fa-university'
    form_layout = [
        Fieldset('必填信息',
                 'warehouse_id','warehouse_name', 'category', 'order_status'),
        Fieldset(None,
                 'creator', 'is_delete', **{"style": "display:None"}),
    ]

    def save_models(self):
        obj = self.new_obj
        request = self.request
        obj.creator = request.user.username
        obj.save()
        super(WarehouseInfoAdmin, self).save_models()


class WarehouseGeneralAdmin(object):
    list_display = ['warehouse_id', 'warehouse_name', 'city', 'category', 'order_status']
    list_filter = ['category', 'order_status']
    search_fields = ['warehouse_name']
    relfield_style = 'fk-ajax'
    # model_icon = 'fa fa-university'
    form_layout = [
        Fieldset('必填信息',
                 'warehouse_id','warehouse_name', 'category', 'order_status'),
        Fieldset(None,
                 'creator', 'is_delete', **{"style": "display:None"}),
    ]

    def has_add_permission(self):
        # 禁用添加按钮
        return False

    def queryset(self):
        queryset = super(WarehouseGeneralAdmin, self).queryset()
        queryset = queryset.filter(category=0)
        return queryset


class WarehouseManuAdmin(object):
    list_display = ['warehouse_id', 'warehouse_name', 'city', 'category', 'order_status']
    list_filter = ['category', 'order_status']
    search_fields = ['warehouse_name']
    relfield_style = 'fk-ajax'
    # model_icon = 'fa fa-university'
    form_layout = [
        Fieldset('必填信息',
                 'warehouse_id','warehouse_name', 'category', 'order_status'),
        Fieldset(None,
                 'creator', 'is_delete', **{"style": "display:None"}),
    ]

    def has_add_permission(self):
        # 禁用添加按钮
        return False

    def queryset(self):
        queryset = super(WarehouseManuAdmin, self).queryset()
        queryset = queryset.filter(category=1)
        return queryset


class WarehouseVirtualAdmin(object):
    list_display = ['warehouse_id', 'warehouse_name', 'city', 'category', 'order_status']
    list_filter = ['category', 'order_status']
    search_fields = ['warehouse_name']
    relfield_style = 'fk-ajax'
    # model_icon = 'fa fa-university'
    form_layout = [
        Fieldset('必填信息',
                 'warehouse_id','warehouse_name', 'category', 'order_status'),
        Fieldset(None,
                 'creator', 'is_delete', **{"style": "display:None"}),
    ]

    def has_add_permission(self):
        # 禁用添加按钮
        return False

    def queryset(self):
        queryset = super(WarehouseVirtualAdmin, self).queryset()
        queryset = queryset.filter(category=2)
        return queryset


xadmin.site.register(WarehouseGeneral, WarehouseGeneralAdmin)
xadmin.site.register(WarehouseManu, WarehouseManuAdmin)
xadmin.site.register(WarehouseVirtual, WarehouseVirtualAdmin)
xadmin.site.register(WarehouseInfo, WarehouseInfoAdmin)