# coding: utf-8
# @Time : 2020/5/6 10:02 PM
# @Author: Hann
# @File: specialvaso.py


import xadmin
from xadmin.views import BaseAdminPlugin, ListAdminView
from django.template import loader
from xadmin.plugins.utils import get_context_dict


class SpecialCCSOPlugin(BaseAdminPlugin):
    special_ccso = False

    def init_request(self, *args, **kwargs):
        return bool(self.special_ccso)

    def block_top_toolbar(self, context, nodes):
        nodes.append(loader.render_to_string('xadmin/specialccso/specialccso.html', context=get_context_dict(context)))


xadmin.site.register_plugin(SpecialCCSOPlugin, ListAdminView)
