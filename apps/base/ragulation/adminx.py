# -*- coding: utf-8 -*-
# @Time    : 2019/11/21 20:59
# @Author  : Hann
# @Site    : 
# @File    : adminx.py
# @Software: PyCharm

import datetime, re

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


from apps.base.ragulation.models import QuotaDeInfo, QuotaDeValidInfo


class QuotaDeInfoAdmin(object):
    list_display = ['order_status', 'maturity', 'quota_name', 'department', 'quota', 'category', 'creator', 'create_time']
    list_filter = ['department', 'maturity', 'quota', 'category', 'create_time']
    search_fields = ['quota_name']
    form_layout = [
        Fieldset('必填信息',
                 'quota_name', 'department', 'quota', 'maturity', 'category', 'order_status', 'creator'),
        Fieldset(None,
                 'is_delete', **{"style": "display:None"}),
    ]
    readonly_fields = ['order_status', 'maturity', 'quota_name', 'department', 'quota', 'category', 'creator', 'create_time',]

    def save_models(self):
        obj = self.new_obj
        request = self.request
        obj.creator = request.user.username
        obj.save()
        super().save_models()

    def has_add_permission(self):
        # 禁用添加按钮
        return False


class QuotaDeValidInfoAdmin(object):
    list_display = ['order_status', 'maturity', 'quota_name', 'department', 'quota', 'category', 'creator', 'create_time']
    list_filter = ['department', 'maturity', 'quota', 'category', 'create_time']
    search_fields = ['quota_name']
    date_hierarchy = 'maturity'
    form_layout = [
        Fieldset('必填信息',
                 'quota_name', 'department', 'quota', 'maturity', 'category', 'order_status'),
        Fieldset(None,
                 'creator', 'is_delete', **{"style": "display:None"}),
    ]

    def save_models(self):
        obj = self.new_obj
        request = self.request
        obj.creator = request.user.username
        obj.save()
        super().save_models()

    def queryset(self):
        queryset = super(QuotaDeValidInfoAdmin, self).queryset()
        queryset = queryset.filter(order_status=1)
        for obj in queryset:
            current_time = datetime.datetime.now()
            maturity = obj.maturity
            d_val = (maturity - current_time).days
            if d_val < 1:
                obj.order_status = 2
                obj.save()
        queryset = queryset.filter(order_status=1)
        return queryset


xadmin.site.register(QuotaDeValidInfo, QuotaDeValidInfoAdmin)
xadmin.site.register(QuotaDeInfo, QuotaDeInfoAdmin)
