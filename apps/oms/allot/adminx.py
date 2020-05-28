# -*- coding: utf-8 -*-
# @Time    : 2019/12/28 14:53
# @Author  : Hann
# @Site    : 
# @File    : adminx.py
# @Software: PyCharm


import re, datetime
import pandas as pd
import xadmin

from django.core.exceptions import PermissionDenied
from django.db.models import Q, Sum, Count, Avg
from django.db import router
from django.utils.encoding import force_text
from django.template.response import TemplateResponse
from django.contrib.admin.utils import get_deleted_objects
from django.db import models

from xadmin.plugins.actions import BaseActionView
from xadmin.views.base import filter_hook
from xadmin.util import model_ngettext
from xadmin.layout import Fieldset

from .models import VAllotSOInfo, VASOCheck, VASOHandle, VAllotSIInfo, VASICheck, VASIMine
from apps.wms.stock.models import DeptStockInfo, StockInfo
from apps.base.relationship.models import DeptToVW, DeptToW
from apps.base.department.models import CentreInfo

ACTION_CHECKBOX_NAME = '_selected_action'


class RejectSelectedAction(BaseActionView):

    action_name = "reject_selected"
    description = '驳回选中的单据'

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
                if obj.order_status > 0:
                    obj.order_status -= 1
                    obj.save()
                    if obj.order_status == 0:
                        self.message_user("%s 取消成功" % obj.order_id, "success")
                    else:
                        self.message_user("%s 驳回上一级成功" % obj.order_id, "success")
                else:
                    n -= 1
                    self.message_user("%s 单据状态错误，请检查，驳回出错。" % obj.order_id, "error")
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


# 入库单关联模块，让入库单关联出库单
class VASICheckInline(object):
    model = VASICheck
    exclude = ['va_stockin', 'order_id', 'order_category', 'ori_centre', 'goods_id', 'goods_name',
               'warehouse', 'order_status', 'mistake_tag', 'creator', 'ori_vwarehouse', 'is_delete', 'vwarehouse']

    extra = 1
    style = 'table'

    def queryset(self):
        queryset = super(VASICheckInline, self).queryset()
        queryset = queryset.filter(is_delete=0, order_status=1)
        return queryset


# 递交虚拟调拨单
class AOSubmitAction(BaseActionView):
    action_name = "submit_oa"
    description = "提交选中的分配单"
    model_perm = 'change'
    icon = "fa fa-check-square-o"

    modify_models_batch = False

    @filter_hook
    def do_action(self, queryset):
        if not self.has_change_permission():
            raise PermissionDenied
        n = queryset.count()
        if n:
            if self.modify_models_batch:
                self.log('change',
                         '批量审核了 %(count)d %(items)s.' % {"count": n, "items": model_ngettext(self.opts, n)})
                queryset.update(status=2)
            else:
                for obj in queryset:
                    self.log('change', '', obj)
                    obj.dept_stock.quantity = obj.dept_stock.quantity - obj.quantity
                    if obj.dept_stock.quantity < 0:
                        self.message_user("%s 可调拨数量不足，修正调拨数量" % obj.order_id, "error")
                        obj.mistake_tag = 1
                        obj.save()
                        continue
                    else:
                        try:
                            obj.dept_stock.save()
                        except Exception as e:
                            self.message_user("%s 更新虚拟库存错误, %s" % (obj.order_id, e), "error")
                            obj.mistake_tag = 2
                            obj.save()
                            continue
                    if obj.centre.category == 1:
                        _q_stock = StockInfo.objects.filter(goods_name=obj.goods_name, warehouse=obj.warehouse)
                        if _q_stock.exists():
                            stock = _q_stock[0]
                            stock.undistributed -= obj.quantity
                            if stock.undistributed < 0:
                                self.message_user("%s 实仓可调拨库存数量错误, %s" % (obj.order_id, e), "error")
                                obj.mistake_tag = 4
                                obj.save()
                                continue
                            else:
                                try:
                                    stock.save()
                                except Exception as e:
                                    self.message_user("%s 实仓可调拨保存错误, %s" % (obj.order_id, e), "error")
                                    obj.mistake_tag = 6
                                    obj.save()
                                    continue
                        else:
                            self.message_user("%s 查不到实仓可调拨货品, %s" % (obj.order_id, e), "error")
                            obj.mistake_tag = 5
                            obj.save()
                            continue
                        pass
                    obj.order_status = 2
                    obj.mistake_tag = 0
                    try:
                        obj.save()
                    except Exception as e:
                        self.message_user("%s 单据保存出错, %s" % (obj.order_id, e), "error")
                        obj.mistake_tag = 3
                        obj.save()
                        continue

            self.message_user("成功提交 %(count)d %(items)s." % {"count": n, "items": model_ngettext(self.opts, n)},
                              'success')

        return None


class VASOCheckAdmin(object):
    list_display = ['order_id', 'order_status', 'mistake_tag', 'goods_name', 'warehouse', 'vwarehouse', 'centre',
                    'goods_id', 'quantity', 'undistributed', 'dept_stock_quantity', 'memorandum']
    list_filter = ['order_status', 'mistake_tag', 'goods_name__goods_name', 'warehouse__warehouse_name',
                   'vwarehouse__warehouse_name', 'centre__name', 'goods_id', 'quantity']

    actions = [AOSubmitAction, RejectSelectedAction]
    readonly_fields = ['dept_stock', 'order_id', 'order_category', 'centre', 'goods_id', 'goods_name',
                       'undistributed', 'warehouse', 'vwarehouse', 'mistake_tag', 'order_status', 'is_delete',
                       'creator', 'create_time', 'update_time']

    form_layout = [
        Fieldset('主要信息',
                  'order_id', 'goods_name', 'order_category',  'quantity', 'undistributed', 'warehouse', 'vwarehouse', 'centre'),
        Fieldset('一般信息',
                 'memorandum'),
        Fieldset(None,
                 'mistake_tag', 'creator', 'order_status', 'is_delete', 'goods_id', 'dept_stock', **{"style": "display:None"}),
    ]

    def queryset(self):
        queryset = super(VASOCheckAdmin, self).queryset()
        queryset = queryset.filter(is_delete=0, order_status=1)
        return queryset

    def save_models(self):
        obj = self.new_obj
        obj.undistributed = obj.quantity
        obj.save()
        super(VASOCheckAdmin, self).save_models()

    def has_add_permission(self):
        # 禁用添加按钮
        return False


# 未分配调拨出库单
class VASOHandleAdmin(object):
    list_display = ['order_id', 'order_status', 'mistake_tag', 'goods_name', 'warehouse', 'vwarehouse', 'centre',
                    'goods_id', 'quantity', 'undistributed', 'memorandum']
    list_filter = ['order_status', 'mistake_tag', 'goods_name__goods_name', 'warehouse__warehouse_name',
                   'vwarehouse__warehouse_name', 'centre__name', 'goods_id', 'quantity']
    inlines = [VASICheckInline, ]
    actions = []
    readonly_fields = ['dept_stock', 'order_id', 'order_category', 'centre', 'goods_id', 'goods_name', 'quantity',
                       'undistributed', 'warehouse', 'vwarehouse', 'mistake_tag', 'order_status', 'is_delete',
                       'creator', 'create_time', 'update_time']

    form_layout = [
        Fieldset('主要信息',
                  'order_id', 'goods_name', 'goods_id', 'order_category',  'quantity', 'undistributed', 'warehouse', 'vwarehouse', 'centre'),
        Fieldset('一般信息',
                 'memorandum'),
        Fieldset(None,
                 'mistake_tag', 'creator', 'order_status', 'is_delete', 'dept_stock', 'create_time', 'update_time', **{"style": "display:None"}),
    ]
    batch_data = True
    special_vasi = True
    ids = []

    def post(self, request, *args, **kwargs):
        ids = request.POST.get('ids', None)
        special_tag = request.POST.get('special_tag', None)
        if special_tag:
            _q_warehouse = DeptToW.objects.all()
            warehouse_list = [warehouse.warehouse for warehouse in _q_warehouse]
            queryset = VAllotSOInfo.objects.filter(order_status=2, warehouse__in=warehouse_list)
            n = queryset.count()
            if n:
                i = 0
                for obj in queryset:
                    order_si = VAllotSIInfo()
                    i += 1
                    self.log('change', '', obj)
                    prefix = "AI"
                    serial_number = str(datetime.datetime.now()).replace("-", "").replace(" ", "").replace(":",
                                                                                                           "").replace(
                        ".", "")[:12]
                    suffix = 1000 + i
                    order_id = prefix + str(serial_number) + str(suffix)
                    order_si.order_id = order_id
                    _q_centre = DeptToW.objects.filter(warehouse=obj.warehouse)
                    centre_num = _q_centre.count()
                    if _q_centre.exists() and centre_num == 1:
                        des_centre = _q_centre[0].centre
                    else:
                        self.message_user("%s 中心对应实仓出错, %s" % (obj.order_id, e), "error")
                        obj.mistake_tag = 2
                        obj.save()
                        continue
                    _q_vwarehouse = DeptToVW.objects.filter(centre=des_centre)
                    if _q_vwarehouse.exists():
                        des_vwarehouse = _q_vwarehouse[0].warehouse
                    else:
                        self.message_user("%s 部门对应中心仓出错, %s" % (obj.order_id, e), "error")
                        obj.mistake_tag = 2
                        obj.save()
                        continue

                    order_si.warehouse = obj.warehouse
                    order_si.ori_vwarehouse = obj.vwarehouse
                    order_si.ori_centre = obj.centre
                    order_si.centre = des_centre
                    order_si.vwarehouse = des_vwarehouse
                    order_si.quantity = obj.quantity
                    order_si.creator = request.user.username
                    order_si.goods_name = obj.goods_name
                    order_si.goods_id = obj.goods_id
                    order_si.va_stockout = obj
                    try:
                        order_si.save()
                    except Exception as e:
                        self.message_user("%s 创建虚拟入库单出错, %s" % (obj.order_id, e), "error")
                        continue

                self.message_user("成功生成 %(count)d %(items)s." % {"count": n, "items": model_ngettext(self.opts, n)},
                                  'success')
        if ids is not None:
            if " " in ids:
                ids = ids.split(" ")
                for i in ids:
                    if not re.match(r'^.{3,30}$', i):
                        self.message_user('%s包含错误的货品编号，请检查' % str(ids), 'error')
                        break

                self.ids = ids
                self.queryset()

        return super(VASOHandleAdmin, self).post(request, *args, **kwargs)

    def queryset(self):
        queryset = super(VASOHandleAdmin, self).queryset()
        queryset.filter(is_delete=0, order_status=2, undistributed=0).update(order_status=3)

        if self.ids:
            queryset = queryset.filter(is_delete=0, order_status=2, goods_id__in=self.ids)
        else:
            queryset = queryset.filter(is_delete=0, order_status=2)
        return queryset

    def save_related(self):

        for i in range(self.formsets[0].forms.__len__()):
            request = self.request
            obj = self.formsets[0].forms[i].instance
            _q_vwarehouse = DeptToVW.objects.filter(centre=obj.centre)
            if _q_vwarehouse.exists():
                obj.vwarehouse = _q_vwarehouse[0].warehouse

            if not obj.order_id:
                prefix = "AI"
                serial_number = str(datetime.datetime.now()).replace("-", "").replace(" ", "").replace(":", "").replace(".", "")[:12]
                suffix = 1000 + i
                order_id = prefix + str(serial_number) + str(suffix)
                obj.order_id = order_id

            obj.warehouse = self.org_obj.warehouse
            obj.ori_vwarehouse = self.org_obj.vwarehouse
            obj.ori_centre = self.org_obj.centre
            obj.creator = request.user.username
            obj.goods_name = self.org_obj.goods_name
            obj.goods_id = self.org_obj.goods_id

        super().save_related()


class VAllotSOInfoAdmin(object):
    list_display = ['order_id', 'order_status', 'mistake_tag', 'goods_name', 'warehouse', 'vwarehouse', 'centre',
                    'goods_id', 'quantity', 'undistributed', 'memorandum']
    list_filter = ['order_status', 'mistake_tag', 'goods_name__goods_name', 'warehouse__warehouse_name',
                   'vwarehouse__warehouse_name', 'centre__name', 'goods_id', 'quantity']
    search_fields = ['order_id']
    inlines = [VASICheckInline, ]
    actions = []
    readonly_fields = ['dept_stock', 'order_id', 'order_category', 'centre', 'goods_id', 'goods_name', 'quantity',
                       'undistributed', 'warehouse', 'vwarehouse', 'mistake_tag', 'order_status', 'is_delete', 'creator', 'create_time', 'update_time']

    form_layout = [
        Fieldset('主要信息',
                  'order_id', 'goods_name', 'goods_id', 'order_category',  'quantity', 'undistributed', 'warehouse', 'vwarehouse', 'department'),
        Fieldset('一般信息',
                 'memorandum'),
        Fieldset(None,
                 'mistake_tag', 'creator', 'order_status', 'is_delete', 'dept_stock', **{"style": "display:None"}),
    ]


    def has_add_permission(self):
        # 禁用添加按钮
        return False


# 审核虚拟调拨入库单
class VASICheckAction(BaseActionView):
    action_name = "check_va_si"
    description = "提交选中的分配单"
    model_perm = 'change'
    icon = "fa fa-check-square-o"

    modify_models_batch = False

    @filter_hook
    def do_action(self, queryset):
        if not self.has_change_permission():
            raise PermissionDenied
        n = queryset.count()
        if n:
            if self.modify_models_batch:
                self.log('change',
                         '批量审核了 %(count)d %(items)s.' % {"count": n, "items": model_ngettext(self.opts, n)})
                queryset.update(status=2)
            else:
                check_uq = 0
                for obj in queryset:
                    self.log('change', '', obj)
                    if check_uq:
                        obj.va_stockout.undistributed = check_uq
                    _q_dept_stock = DeptStockInfo.objects.filter(centre=obj.centre, goods_name=obj.goods_name,
                                                                 warehouse=obj.warehouse, vwarehouse=obj.vwarehouse)

                    if _q_dept_stock.exists():
                        dept_stock = _q_dept_stock[0]
                        dept_stock.quantity += obj.quantity
                    else:
                        dept_stock = DeptStockInfo()
                        fields = ['centre', 'goods_name', 'goods_id', 'warehouse', 'vwarehouse', 'quantity']
                        for key in fields:
                            value = getattr(obj, key, None)
                            setattr(dept_stock, key, value)
                    check_uq = obj.va_stockout.undistributed - obj.quantity
                    if check_uq < 0:
                        self.message_user("%s 虚拟入库超过了对应出库数" % obj.order_id, "error")
                        obj.mistake_tag = 1
                        obj.save()
                        n -= 1
                        continue
                    else:
                        try:
                            obj.va_stockout.undistributed = check_uq
                            obj.va_stockout.save()
                        except Exception as e:
                            self.message_user("%s 更新对应虚拟入库出错, %s" % (obj.order_id, e), "error")
                            obj.mistake_tag = 2
                            obj.save()
                            n -= 1
                            continue
                    try:
                        dept_stock.save()
                    except Exception as e:
                        self.message_user("%s 单据保存出错, %s" % (obj.order_id, e), "error")
                        obj.mistake_tag = 3
                        obj.save()
                        n -= 1
                        continue
                    obj.order_status = 2
                    obj.mistake_tag = 0
                    obj.save()
            self.message_user("成功提交 %(count)d %(items)s." % {"count": n, "items": model_ngettext(self.opts, n)},
                              'success')
        return None


# 修复已出库未入库
class VASIFixAction(BaseActionView):
    action_name = "fix_va_si"
    description = "已出库未入库修复"
    model_perm = 'change'
    icon = "fa fa-check-square-o"

    modify_models_batch = False

    @filter_hook
    def do_action(self, queryset):
        if not self.has_change_permission():
            raise PermissionDenied
        n = queryset.count()
        if n:
            if self.modify_models_batch:
                self.log('change',
                         '批量审核了 %(count)d %(items)s.' % {"count": n, "items": model_ngettext(self.opts, n)})
                queryset.update(status=2)
            else:
                for obj in queryset:
                    _total_si_quantity = obj.va_stockout.vallotsiinfo_set.all().filter(order_status__in=[1, 2, 3]).aggregate(sum_quantity=Sum('quantity'))['sum_quantity']
                    if not _total_si_quantity:
                        _total_si_quantity = 0
                    if _total_si_quantity > obj.va_stockout.quantity:
                        self.message_user("%s 虚拟入库确实超过了对应出库数，请查看" % obj.order_id, "error")
                        obj.mistake_tag = 1
                        obj.save()
                        n -= 1
                        continue
                    else:
                        _total_si_complete_quantity = obj.va_stockout.vallotsiinfo_set.all().filter(order_status__in=[2, 3]).aggregate(sum_quantity=Sum('quantity'))['sum_quantity']
                        if not _total_si_complete_quantity:
                            _total_si_complete_quantity = 0
                        obj.va_stockout.undistributed = obj.va_stockout.quantity - _total_si_complete_quantity
                        obj.va_stockout.save()

            self.message_user("成功提交 %(count)d %(items)s." % {"count": n, "items": model_ngettext(self.opts, n)},
                              'success')
        return None


# 调拨入库单审核界面
class VASICheckAdmin(object):
    list_display = ['order_id', 'order_status', 'mistake_tag',   'centre', 'quantity', 'goods_name', 'goods_id',
                     'vwarehouse', 'warehouse',   'va_stockout',
                    'ori_centre', 'ori_vwarehouse', 'order_category', 'memorandum', ]
    list_filter = ['order_status', 'mistake_tag', 'order_category', 'centre__name', 'ori_centre__name', 'ori_vwarehouse__warehouse_name', 'vwarehouse__warehouse_name', 'warehouse__warehouse_name','goods_name__goods_name', 'goods_id',]
    search_fields = ['order_id', 'goods_id']
    actions = [VASICheckAction, VASIFixAction, RejectSelectedAction]
    list_editable = ['memorandum', 'quantity']
    readonly_fields = ['va_stockout', 'order_id', 'order_category', 'ori_centre','ori_vwarehouse', 'centre', 'goods_id',
                       'goods_name',  'warehouse', 'vwarehouse', 'order_status', 'mistake_tag']
    form_layout = [
        Fieldset('主要信息',
                  'order_id', 'goods_name', 'order_category',  'quantity', 'ori_centre', 'ori_vwarehouse', 'warehouse', 'vwarehouse', 'centre'),
        Fieldset('一般信息',
                 'memorandum'),
        Fieldset(None,
                 'va_stockout', 'mistake_tag', 'creator', 'order_status', 'is_delete', **{"style": "display:None"}),
    ]
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
        return super(VASICheckAdmin, self).post(request, *args, **kwargs)

    def handle_upload_file(self, _file):
        INIT_FIELDS_DIC = {
            '单据类型': 'order_category',
            '目的中心': 'centre',
            '入库数量': 'quantity',
            '关联出库单': 'va_stockout',
        }
        ALLOWED_EXTENSIONS = ['xls', 'xlsx']
        report_dic = {"successful": 0, "discard": 0, "false": 0, "repeated": 0, "error": []}

        if '.' in _file.name and _file.name.rsplit('.')[-1] in ALLOWED_EXTENSIONS:
            with pd.ExcelFile(_file) as xls:
                df = pd.read_excel(xls, sheet_name=0)
                FILTER_FIELDS = ['单据类型',  '目的中心', '入库数量', '关联出库单']
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
                _ret_verify_field = VASICheck.verify_mandatory(columns_key)
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
                _ret_verify_field = VASICheck.verify_mandatory(columns_key)
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
        i = 0
        for row in resource:
            i += 1
            order = VASICheck()  # 创建表格每一行为一个对象
            for k, v in row.items():
                if not row[k]:
                    report_dic["false"] += 1
                    report_dic["error"].append('不允许为空：%s' % row[k])
                    continue
                if k == 'quantity':
                    row[k] = int(str(v).replace("'", '').replace(' ', ''))
                else:
                    row[k] = str(v).replace("'", '').replace(' ', '')


            prefix = "AI"
            serial_number = str(datetime.datetime.now()).replace("-", "").replace(" ", "").replace(":", "").replace(".", "")[:12]
            suffix = 1000 + i
            order_id = prefix + str(serial_number) + str(suffix)
            order.order_id = order_id

            _q_centre = CentreInfo.objects.filter(name=row['centre'])
            if _q_centre.exists():
                centre = _q_centre[0]
            else:
                report_dic["false"] += 1
                report_dic["error"].append('不存在此部门：%s' % row['centre'])
                continue

            _q_dept_warehouse = DeptToVW.objects.filter(centre=centre)
            if _q_dept_warehouse.exists():
                vwarehouse = _q_dept_warehouse[0].warehouse
            else:
                report_dic["false"] += 1
                report_dic["error"].append('部门不存在部门仓：%s，此案创建部门仓再操作！' % row['department'])
                continue

            order.centre = centre
            order.vwarehouse = vwarehouse
            order.quantity = row['quantity']

            _q_va_stockout = VASOHandle.objects.filter(order_id=row['va_stockin'])
            if _q_va_stockout.exists():
                va_stockout = _q_va_stockout[0]
            else:
                report_dic["false"] += 1
                report_dic["error"].append('不存在此虚拟出库单：%s' % row['va_stockin'])
                continue

            order.goods_name = va_stockout.goods_name
            order.goods_id = va_stockout.goods_id
            order.ori_centre = va_stockout.centre
            order.warehouse = va_stockout.warehouse
            order.ori_vwarehouse = va_stockout.vwarehouse
            order.va_stockout = va_stockout

            try:
                order.creator = self.request.user.username
                order.save()
                report_dic["successful"] += 1
            # 保存出错，直接错误条数计数加一。
            except Exception as e:
                report_dic["error"].append(e)
                report_dic["false"] += 1
        return report_dic

    def queryset(self):
        queryset = super(VASICheckAdmin, self).queryset()
        queryset = queryset.filter(is_delete=0, order_status=1)
        return queryset

    def has_add_permission(self):
        # 禁用添加按钮
        return False


# 处理本部门虚拟调拨入库单
class VASIHandleAction(BaseActionView):
    action_name = "handle_va_si"
    description = "提交选中的分配单"
    model_perm = 'change'
    icon = "fa fa-check-square-o"

    modify_models_batch = True

    @filter_hook
    def do_action(self, queryset):
        if not self.has_change_permission():
            raise PermissionDenied
        n = queryset.count()
        if n:
            if self.modify_models_batch:
                self.log('change',
                         '批量审核了 %(count)d %(items)s.' % {"count": n, "items": model_ngettext(self.opts, n)})
                queryset.update(order_status=3)
            else:
                for obj in queryset:
                    self.log('change', '', obj)

                obj.order_status = 2
                obj.mistake_tag = 0
                obj.save()
            self.message_user("成功提交 %(count)d %(items)s." % {"count": n, "items": model_ngettext(self.opts, n)},
                              'success')
        return None


# 未处理虚拟入库列表
class VASIMineAdmin(object):
    list_display = ['order_id', 'order_status', 'mistake_tag', 'order_category', 'ori_centre', 'ori_vwarehouse',
                    'vwarehouse', 'warehouse', 'goods_name', 'goods_id', 'quantity', 'centre', 'va_stockout',
                    'memorandum', ]
    list_filter = ['order_status', 'mistake_tag', 'order_category', 'centre__name', 'ori_centre__name', 'ori_vwarehouse__warehouse_name', 'vwarehouse__warehouse_name', 'warehouse__warehouse_name','goods_name__goods_name', 'goods_id',]
    search_fields = ['order_id', 'goods_id']
    actions = [VASIHandleAction, ]
    list_editable = ['memorandum']
    readonly_fields = ['va_stockout', 'order_id', 'order_category', 'ori_centre','ori_vwarehouse', 'centre', 'goods_id',
                       'goods_name', 'quantity', 'warehouse', 'vwarehouse', 'order_status', 'mistake_tag']
    form_layout = [
        Fieldset('主要信息',
                  'order_id', 'goods_name', 'order_category',  'quantity', 'ori_centre', 'ori_vwarehouse', 'warehouse', 'vwarehouse', 'centre'),
        Fieldset('一般信息',
                 'memorandum'),
        Fieldset(None,
                 'va_stockout', 'mistake_tag', 'creator', 'order_status', 'is_delete', 'dept_stock', **{"style": "display:None"}),
    ]

    def queryset(self):
        queryset = super(VASIMineAdmin, self).queryset().filter(is_delete=0, order_status=2)
        if self.request.user.is_superuser != 1:
            queryset = queryset.filter(centre=self.request.user.department.centre)
        return queryset

    def has_add_permission(self):
        # 禁用添加按钮
        return False


class VAllotSIInfoAdmin(object):
    list_display = ['order_id', 'order_status', 'mistake_tag', 'order_category', 'ori_centre',
                    'ori_vwarehouse', 'vwarehouse', 'warehouse', 'goods_name', 'goods_id', 'quantity', 'centre',
                    'memorandum', ]
    list_filter = ['order_status', 'mistake_tag', 'order_category', 'centre__name', 'ori_centre__name', 'ori_vwarehouse__warehouse_name', 'vwarehouse__warehouse_name', 'warehouse__warehouse_name','goods_name__goods_name', 'goods_id',]
    search_fields = ['order_id', 'goods_id']
    readonly_fields = ['va_stockout', 'order_id', 'order_category', 'ori_centre','ori_vwarehouse', 'centre', 'goods_id',
                       'goods_name', 'quantity', 'warehouse', 'vwarehouse', 'order_status', 'mistake_tag']
    form_layout = [
        Fieldset('主要信息',
                  'order_id', 'goods_name', 'order_category',  'quantity', 'ori_centre', 'ori_vwarehouse', 'warehouse', 'vwarehouse', 'centre'),
        Fieldset('一般信息',
                 'memorandum'),
        Fieldset(None,
                 'va_stockout', 'mistake_tag', 'creator', 'order_status', 'is_delete', 'dept_stock', **{"style": "display:None"}),
    ]

    def has_add_permission(self):
        # 禁用添加按钮
        return False


xadmin.site.register(VASOCheck, VASOCheckAdmin)
xadmin.site.register(VASOHandle, VASOHandleAdmin)
xadmin.site.register(VAllotSOInfo, VAllotSOInfoAdmin)
xadmin.site.register(VASICheck, VASICheckAdmin)
xadmin.site.register(VASIMine, VASIMineAdmin)
xadmin.site.register(VAllotSIInfo, VAllotSIInfoAdmin)



