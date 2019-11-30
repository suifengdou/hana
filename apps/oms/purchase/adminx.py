# -*- coding: utf-8 -*-
# @Time    : 2019/11/28 20:56
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

from .models import PurchaseInfo, PurchasePending


ACTION_CHECKBOX_NAME = '_selected_action'


class PurchaseInfoAdmin(object):
    pass


class PurchasePendingAdmin(object):
    pass


xadmin.site.register(PurchaseInfo, PurchaseInfoAdmin)
xadmin.site.register(PurchasePending, PurchasePendingAdmin)


