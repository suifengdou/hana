# coding: utf-8
# @Time : 2019/11/10 10:43 AM
# @Author: Hann
# @File: xadmin.py

import xadmin

from xadmin import views


class GlobalSettings(object):
    site_title = 'UT后台管理系统'
    site_footer = 'UltraTool V0.5.1.35'
    menu_style = 'accordion'


xadmin.site.register(views.CommAdminView, GlobalSettings)


