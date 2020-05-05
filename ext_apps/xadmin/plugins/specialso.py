# coding: utf-8
# @Time : 2020/5/2 4:12 PM
# @Author: Hann
# @File: specialso.py

import xadmin
from xadmin.views import BaseAdminPlugin, ListAdminView
from django.template import loader
from xadmin.plugins.utils import get_context_dict


class SpecialSOPlugin(BaseAdminPlugin):
    special_so = False

    def init_request(self, *args, **kwargs):
        return bool(self.special_so)

    def block_top_toolbar(self, context, nodes):
        nodes.append(loader.render_to_string('xadmin/specialso/specialso.html', context=get_context_dict(context)))


xadmin.site.register_plugin(SpecialSOPlugin, ListAdminView)
