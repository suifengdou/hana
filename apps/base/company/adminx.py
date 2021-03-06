# -*- coding: utf-8 -*-
# @Time    : 2019/11/17 19:36
# @Author  : Hann
# @Site    : 
# @File    : adminx.py
# @Software: PyCharm
import re
import pandas as pd
import datetime

from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.db import router
from django.utils.encoding import force_text
from django.template.response import TemplateResponse
from django.contrib.admin.utils import get_deleted_objects


import xadmin
from .models import CompanyInfo, LogisticsInfo, ManuInfo, WareInfo, MineInfo
from xadmin.plugins.actions import BaseActionView
from xadmin.views.base import filter_hook
from xadmin.util import model_ngettext
from xadmin.layout import Fieldset

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


class LogisticsInfoAdmin(object):
    list_display = ['company_name', 'company', 'tax_fil_number', 'order_status', 'category', 'create_time', 'creator']
    relfield_style = 'fk-ajax'

    def queryset(self):
        queryset = super(LogisticsInfoAdmin, self).queryset()
        queryset = queryset.filter(category=1)
        return queryset

    def has_add_permission(self):
        # 禁用添加按钮
        return False


class ManuInfoAdmin(object):
    list_display = ['company_name', 'company_id', 'tax_fil_number', 'order_status', 'category', 'create_time', 'creator']
    relfield_style = 'fk-ajax'

    def queryset(self):
        queryset = super(ManuInfoAdmin, self).queryset()
        queryset = queryset.filter(category=3)
        return queryset

    def has_add_permission(self):
        # 禁用添加按钮
        return False


class WareInfoAdmin(object):
    list_display = ['company_name', 'company_id', 'tax_fil_number', 'order_status', 'category', 'create_time', 'creator']
    relfield_style = 'fk-ajax'

    def queryset(self):
        queryset = super(WareInfoAdmin, self).queryset()
        queryset = queryset.filter(category=2)
        return queryset

    def has_add_permission(self):
        # 禁用添加按钮
        return False


class MineInfoAdmin(object):
    list_display = ['company_name', 'company_id', 'tax_fil_number', 'order_status', 'category', 'create_time', 'creator']
    relfield_style = 'fk-ajax'

    def queryset(self):
        queryset = super(MineInfoAdmin, self).queryset()
        queryset = queryset.filter(category=0)
        return queryset

    def has_add_permission(self):
        # 禁用添加按钮
        return False



class CompanyInfoAdmin(object):
    list_display = ['company_name', 'company_id', 'tax_fil_number', 'order_status', 'category', 'create_time', 'creator']
    list_filter = ['category']
    search_fields = ['company_name']
    form_layout = [
        Fieldset('必填信息',
                 'company_name', 'order_status', 'category'),
        Fieldset(None,
                 'creator', 'is_delete', **{"style": "display:None"}),
    ]
    actions = [RejectSelectedAction]
    import_data = True

    def post(self, request, *args, **kwargs):

        file = request.FILES.get('file', None)
        if file:
            result = self.handle_upload_file(file)
            if isinstance(result, int):
                self.message_user('导入成功数据%s条' % result['successful'], 'success')
                if result['false'] > 0:
                    self.message_user('导入失败数据%s条,主要的错误是%s' % (result['false'], result['error']), 'warning')
                if result['repeated'] > 0:
                    self.message_user('包含更新重复数据%s条' % result['repeated'], 'error')
            else:
                self.message_user('结果提示：%s' % result)
        return super(CompanyInfoAdmin, self).post(request, *args, **kwargs)

    def handle_upload_file(self, _file):
        INIT_FIELDS_DIC = {
            '公司简称': 'company_name',
            '公司类型': 'category',
        }

        ALLOWED_EXTENSIONS = ['xls', 'xlsx']
        report_dic = {"successful": 0, "discard": 0, "false": 0, "repeated": 0, "error": []}

        if '.' in _file.name and _file.name.rsplit('.')[-1] in ALLOWED_EXTENSIONS:
            with pd.ExcelFile(_file) as xls:
                df = pd.read_excel(xls, sheet_name=0)
                FILTER_FIELDS = ['公司简称', '公司类型']

                try:
                    df = df[FILTER_FIELDS]
                except Exception as e:
                    report_dic["error"].append(e)
                    return report_dic

                # 获取表头，对表头进行转换成数据库字段名
                columns_key = df.columns.values.tolist()
                for i in range(len(columns_key)):
                    columns_key[i] = columns_key[i].replace(' ', '').replace('=', '')

                for i in range(len(columns_key)):
                    if INIT_FIELDS_DIC.get(columns_key[i], None) is not None:
                        columns_key[i] = INIT_FIELDS_DIC.get(columns_key[i])

                # 验证一下必要的核心字段是否存在
                _ret_verify_field = CompanyInfo.verify_mandatory(columns_key)
                if _ret_verify_field is not None:
                    return _ret_verify_field

                # 更改一下DataFrame的表名称
                columns_key_ori = df.columns.values.tolist()
                ret_columns_key = dict(zip(columns_key_ori, columns_key))
                df.rename(columns=ret_columns_key, inplace=True)

                # 获取导入表格的字典，每一行一个字典。这个字典最后显示是个list
                _ret_list = df.to_dict(orient='records')
                intermediate_report_dic = self.save_resources(_ret_list)
                for k, v in intermediate_report_dic.items():
                    if k == "error":
                        if intermediate_report_dic["error"]:
                            report_dic[k].append(v)
                    else:
                        report_dic[k] += v
                return report_dic

        # 以下是csv处理逻辑，和上面的处理逻辑基本一致。
        elif '.' in _file.name and _file.name.rsplit('.')[-1] == 'csv':
            df = pd.read_csv(_file, encoding="GBK", chunksize=300)

            for piece in df:
                # 获取表头
                columns_key = piece.columns.values.tolist()
                # 剔除表头中特殊字符等于号和空格
                for i in range(len(columns_key)):
                    columns_key[i] = columns_key[i].replace(' ', '').replace('=', '')
                # 循环处理对应的预先设置，转换成数据库字段名称
                for i in range(len(columns_key)):
                    if INIT_FIELDS_DIC.get(columns_key[i], None) is not None:
                        columns_key[i] = INIT_FIELDS_DIC.get(columns_key[i])
                # 直接调用验证函数进行验证
                _ret_verify_field = CompanyInfo.verify_mandatory(columns_key)
                if _ret_verify_field is not None:
                    return _ret_verify_field
                # 验证通过进行重新处理。
                columns_key_ori = piece.columns.values.tolist()
                ret_columns_key = dict(zip(columns_key_ori, columns_key))
                piece.rename(columns=ret_columns_key, inplace=True)
                _ret_list = piece.to_dict(orient='records')
                intermediate_report_dic = self.save_resources(_ret_list)
                for k, v in intermediate_report_dic.items():
                    if k == "error":
                        if intermediate_report_dic["error"]:
                            report_dic[k].append(v)
                    else:
                        report_dic[k] += v
            return report_dic

        else:
            return "只支持excel和csv文件格式！"

    def save_resources(self, resource):
        # 设置初始报告
        report_dic = {"successful": 0, "discard": 0, "false": 0, "repeated": 0, "error": []}
        CATEGORY = {
            '本埠主体': 0,
            '物流快递': 1,
            '仓库存储': 2,
            '生产制造': 3,
            '其他类型': 4
        }

        # 开始导入数据
        for row in resource:
            # 判断表格尾部
            for k, v in row.items():
                if re.match(r'^=', str(v)):
                    row[k] = v.replace('=', '').replace('"', '')

            company_name = str(row["company_name"])
            category = CATEGORY.get(row['category'], None)
            if not category:
                report_dic["false"] += 1
                report_dic["error"].append('%s 公司类型错误' % q_company)
                continue
            row['category'] = category
            q_company = CompanyInfo.objects.filter(company_name=company_name)
            if q_company.exists():
                report_dic["false"] += 1
                report_dic["error"].append('%s 公司已经存在' % q_company)
                continue

            order = CompanyInfo()  # 创建表格每一行为一个对象

            for k, v in row.items():
                # 查询是否有这个字段属性，如果有就更新到对象。nan, NaT 是pandas处理数据时候生成的。
                if hasattr(order, k):
                    if str(v) in ['nan', 'NaT']:
                        pass
                    else:
                        setattr(order, k, v)  # 更新对象属性为字典对应键值
            try:
                order.creator = self.request.user.username
                order.save()
                report_dic["successful"] += 1
            # 保存出错，直接错误条数计数加一。
            except Exception as e:
                report_dic["error"].append(e)
                report_dic["false"] += 1
        return report_dic

    def save_models(self):
        obj = self.new_obj
        request = self.request
        obj.creator = request.user.username
        obj.save()
        super(CompanyInfoAdmin, self).save_models()






xadmin.site.register(LogisticsInfo, LogisticsInfoAdmin)
xadmin.site.register(ManuInfo, ManuInfoAdmin)
xadmin.site.register(WareInfo, WareInfoAdmin)
xadmin.site.register(MineInfo, MineInfoAdmin)
xadmin.site.register(CompanyInfo, CompanyInfoAdmin)