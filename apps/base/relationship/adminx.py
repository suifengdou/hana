# -*- coding: utf-8 -*-
# @Time    : 2019/11/19 20:14
# @Author  : Hann
# @Site    : 
# @File    : adminx.py
# @Software: PyCharm
import pandas as pd
import re
import datetime
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.db import router
from django.utils.encoding import force_text
from django.template.response import TemplateResponse
from django.contrib.admin.utils import get_deleted_objects


import xadmin
from .models import DeptToW, DeptToVW
from apps.base.department.models import CentreInfo
from apps.base.warehouse.models import WarehouseInfo, WarehouseVirtual
from xadmin.plugins.actions import BaseActionView
from xadmin.views.base import filter_hook
from xadmin.util import model_ngettext
from xadmin.layout import Fieldset

ACTION_CHECKBOX_NAME = '_selected_action'


class DeptToVWAdmin(object):
    list_display = ['order_status', 'centre', 'warehouse', 'create_time', 'creator']
    list_filter = ['order_status']
    search_fields = ['centre__name', 'warehouse__warehouse_name']
    form_layout = [
        Fieldset('必填信息',
                 'centre', 'warehouse', 'order_status'),
        Fieldset(None,
                 'creator', 'is_delete', **{"style": "display:None"}),
    ]
    actions = []
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
        return super(DeptToVWAdmin, self).post(request, *args, **kwargs)

    def handle_upload_file(self, _file):
        INIT_FIELDS_DIC = {
            '中心名称': 'centre',
            '虚拟仓库': 'warehouse',
        }
        ALLOWED_EXTENSIONS = ['xls', 'xlsx']
        report_dic = {"successful": 0, "discard": 0, "false": 0, "repeated": 0, "error": []}

        if '.' in _file.name and _file.name.rsplit('.')[-1] in ALLOWED_EXTENSIONS:
            with pd.ExcelFile(_file) as xls:
                df = pd.read_excel(xls, sheet_name=0)
                FILTER_FIELDS = ['中心名称', '虚拟仓库']

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
                _ret_verify_field = DeptToVW.verify_mandatory(columns_key)
                if _ret_verify_field is not None:
                    report_dic['error'].append(_ret_verify_field)
                    return report_dic

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
                _ret_verify_field = DeptToVW.verify_mandatory(columns_key)
                if _ret_verify_field is not None:
                    report_dic['error'].append(_ret_verify_field)
                    return report_dic

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
            report_dic['error'].append("只支持excel和csv文件格式")
            return report_dic

    def save_resources(self, resource):
        # 设置初始报告
        report_dic = {"successful": 0, "discard": 0, "false": 0, "repeated": 0, "error": []}

        # 开始导入数据
        for row in resource:
            # 判断表格尾部
            order = DeptToVW()  # 创建表格每一行为一个对象
            for k, v in row.items():
                if re.match(r'^=', str(v)):
                    row[k] = v.replace('=', '').replace('"', '')

            centre = str(row["centre"])
            q_centre = CentreInfo.objects.filter(name=centre)
            if q_centre.exists():
                order.centre = q_centre[0]
            else:
                report_dic["false"] += 1
                report_dic["error"].append('%s部门不存在' % centre)
                continue
            vwarehouse = str(row['warehouse'])
            q_vwarehouse = WarehouseVirtual.objects.filter(warehouse_name=vwarehouse)
            if q_vwarehouse.exists():
                order.warehouse = q_vwarehouse[0]
            else:
                report_dic["false"] += 1
                report_dic["error"].append('%s仓库不存在' % vwarehouse)
                continue

            _repeate = DeptToVW.objects.filter(centre=order.centre, warehouse=order.warehouse)
            if _repeate.exists():
                report_dic["false"] += 1
                report_dic["error"].append('%s已经关联过仓库%s' % (centre, vwarehouse))
                continue

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
        super(DeptToVWAdmin, self).save_models()


class DeptToWAdmin(object):
    list_display = ['order_status', 'centre', 'warehouse', 'create_time', 'creator']
    list_filter = ['order_status']
    search_fields = ['centre__name', 'warehouse__warehouse_name']
    form_layout = [
        Fieldset('必填信息',
                 'centre', 'warehouse', 'order_status'),
        Fieldset(None,
                 'creator', 'is_delete', **{"style": "display:None"}),
    ]
    actions = []
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
        return super(DeptToWAdmin, self).post(request, *args, **kwargs)

    def handle_upload_file(self, _file):
        INIT_FIELDS_DIC = {
            '中心名称': 'centre',
            '实物仓库': 'warehouse',
        }
        ALLOWED_EXTENSIONS = ['xls', 'xlsx']
        report_dic = {"successful": 0, "discard": 0, "false": 0, "repeated": 0, "error": []}

        if '.' in _file.name and _file.name.rsplit('.')[-1] in ALLOWED_EXTENSIONS:
            with pd.ExcelFile(_file) as xls:
                df = pd.read_excel(xls, sheet_name=0)
                FILTER_FIELDS = ['中心名称', '实物仓库']

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
                _ret_verify_field = DeptToW.verify_mandatory(columns_key)
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
                _ret_verify_field = DeptToW.verify_mandatory(columns_key)
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

        # 开始导入数据
        for row in resource:
            # 判断表格尾部
            order = DeptToW()  # 创建表格每一行为一个对象
            for k, v in row.items():
                if re.match(r'^=', str(v)):
                    row[k] = v.replace('=', '').replace('"', '')

            centre = str(row["centre"])
            q_centre = CentreInfo.objects.filter(name=centre)
            if q_centre.exists():
                order.centre = q_centre[0]
            else:
                report_dic["false"] += 1
                report_dic["error"].append('%s不存在' % centre)
                continue
            warehouse = str(row['warehouse'])
            q_vwarehouse = WarehouseInfo.objects.filter(warehouse_name=warehouse)
            if q_vwarehouse.exists():
                order.warehouse = q_vwarehouse[0]
            else:
                report_dic["false"] += 1
                report_dic["error"].append('%s仓库不存在' % warehouse)
                continue

            _repeate = DeptToW.objects.filter(centre=order.centre, warehouse=order.warehouse)
            if _repeate.exists():
                report_dic["false"] += 1
                report_dic["error"].append('%s已经关联过仓库%s' % (centre, warehouse))
                continue

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
        super(DeptToWAdmin, self).save_models()


xadmin.site.register(DeptToVW, DeptToVWAdmin)
xadmin.site.register(DeptToW, DeptToWAdmin)

