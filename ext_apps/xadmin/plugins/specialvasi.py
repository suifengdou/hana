# coding: utf-8
# @Time : 2020/5/2 5:44 PM
# @Author: Hann
# @File: specialvasi.py


import xadmin
from xadmin.views import BaseAdminPlugin, ListAdminView
from django.template import loader
from xadmin.plugins.utils import get_context_dict


class SpecialSOPlugin(BaseAdminPlugin):
    special_vasi = False

    def init_request(self, *args, **kwargs):
        return bool(self.special_vasi)

    def block_top_toolbar(self, context, nodes):
        nodes.append(loader.render_to_string('xadmin/specialvasi/specialvasi.html', context=get_context_dict(context)))


xadmin.site.register_plugin(SpecialSOPlugin, ListAdminView)
