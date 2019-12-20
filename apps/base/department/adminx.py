# -*- coding: utf-8 -*-
# @Time    : 2019/11/17 20:00
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
from xadmin.views.edit import ModelFormAdminView

from .models import DepartmentInfo, DepartmentList


ACTION_CHECKBOX_NAME = '_selected_action'


class RejectSelectedAction(BaseActionView):

    action_name = "reject_selected"
    description = '驳回选中的工单'

    delete_confirmation_template = None
    delete_selected_confirmation_template = None

    delete_models_batch = False

    model_perm = 'change'
    icon = 'fa fa-times'

    @filter_hook
    def reject_models(self, queryset):
        n = queryset.count()
        if n:
            for obj in queryset:
                if obj.order_status == 1:
                    obj.order_status -= 1
                    obj.save()
                    if obj.order_status == 0:
                        self.message_user("%s 取消成功" % obj.express_id, "success")
                    else:
                        self.message_user("%s 驳回上一级成功" % obj.express_id, "success")
                else:
                    n -= 1
                    self.message_user("%s 公司状态错误，请检查，取消出错。" % obj.express_id, "error")
            self.message_user("成功驳回 %(count)d %(items)s." % {"count": n, "items": model_ngettext(self.opts, n)},
                              'success')
        return None

    @filter_hook
    def do_action(self, queryset):
        # Check that the user has delete permission for the actual model
        if not self.has_change_permission():
            raise PermissionDenied

        using = router.db_for_write(self.model)

        # Populate deletable_objects, a data structure of all related objects that
        # will also be deleted.
        deletable_objects, model_count, perms_needed, protected = get_deleted_objects(
            queryset, self.opts, self.user, self.admin_site, using)

        # The user has already confirmed the deletion.
        # Do the deletion and return a None to display the change list view again.
        if self.request.POST.get('post'):
            if not self.has_change_permission():
                raise PermissionDenied
            self.reject_models(queryset)
            # Return None to display the change list page again.
            return None

        if len(queryset) == 1:
            objects_name = force_text(self.opts.verbose_name)
        else:
            objects_name = force_text(self.opts.verbose_name_plural)
        perms_needed = []
        if perms_needed or protected:
            title = "Cannot reject %(name)s" % {"name": objects_name}
        else:
            title = "Are you sure?"

        context = self.get_context()
        context.update({
            "title": title,
            "objects_name": objects_name,
            "deletable_objects": [deletable_objects],
            'queryset': queryset,
            "perms_lacking": perms_needed,
            "protected": protected,
            "opts": self.opts,
            "app_label": self.app_label,
            'action_checkbox_name': ACTION_CHECKBOX_NAME,
        })

        # Display the confirmation page
        return TemplateResponse(self.request, self.delete_selected_confirmation_template or
                                self.get_template_list('views/model_reject_selected_confirm.html'), context)


class DepartmentInfoAdmin(object):
    list_display = ['name', 'order_status', 'category','quotavalid', 'create_time', 'creator']
    list_filter = ['category']
    search_fields = ['name']
    form_layout = [
        Fieldset('必填信息',
                 'name', 'order_status', 'category'),
        Fieldset(None,
                 'creator', 'is_delete', **{"style": "display:None"}),
    ]

    def queryset(self):
        if self.request.user.department:
            queryset = super(DepartmentInfoAdmin, self).queryset()
            queryset = queryset.filter(name=self.request.user.department.name)
            return queryset
        else:
            self.message_user("{}没有设置部门，请设置部门再查询".format(self.request.user.username))
            queryset = super(DepartmentInfoAdmin, self).queryset().filter(order_status=9)
            return queryset



class DepartmentListAdmin(object):
    list_display = ['name', 'order_status', 'category', 'create_time', 'creator']
    list_filter = ['category']
    search_fields = ['name']
    form_layout = [
        Fieldset('必填信息',
                 'name', 'category'),
        Fieldset(None,
                 'create_time', 'order_status', 'creator', 'is_delete', **{"style": "display:None"}),
    ]
    readonly_fields = ['name', 'order_status', 'category', 'create_time', 'creator']
    actions = [RejectSelectedAction]

    def save_models(self):
        obj = self.new_obj
        request = self.request
        obj.creator = request.user.username
        obj.save()
        super(DepartmentListAdmin, self).save_models()


xadmin.site.register(DepartmentInfo, DepartmentInfoAdmin)
xadmin.site.register(DepartmentList, DepartmentListAdmin)
