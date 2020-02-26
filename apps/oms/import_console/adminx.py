# coding: utf-8
# @Time : 2020/1/29 9:57 AM
# @Author: Hann
# @File: adminx.py

import re, datetime
import pandas as pd
import xadmin

from django.core.exceptions import PermissionDenied
from django.db.models import Q, Sum, Count, Avg
from django.db import router
from django.utils.encoding import force_text
from django.template.response import TemplateResponse
from django.contrib.admin.utils import get_deleted_objects

from xadmin.plugins.actions import BaseActionView
from xadmin.views.base import filter_hook
from xadmin.util import model_ngettext
from xadmin.layout import Fieldset

from .models import OriStockInUnhandle, OriStockInInfo, OriStockOutUnhandle, OriStockOut, OriPurchaseUnhandle, OriPurchaseInfo
from .models import OriNSSOUnhandle, OriNSStockout, OriNPSIUnhandle, OriNPStockIn, OriRefundUnhandle, OriRefund
from .models import OriPRUnhandle, OriPurRefund, OriALUnhandle, OriAllocation, OriSUUnhandle, OriSurplus, OriLOUnhandle, OirLoss

from apps.oms.convert_console.models import CovertSI, CovertSO
from apps.base.warehouse.models import WarehouseGeneral
from apps.base.goods.models import GoodsInfo
from apps.oms.purchase.models import PurchaseInfo
from apps.base.company.models import ManuInfo, CompanyInfo
from apps.base.department.models import DepartmentInfo

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


# 递交原始采购单
class PurSMAction(BaseActionView):
    action_name = "submit_pur_ori"
    description = "提交选中的单据"
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
                    purchase_order_id = '{0}-{1}'.format(str(obj.order_id), str(obj.detail_num))
                    repeat_queryset = PurchaseInfo.objects.filter(purchase_order_id=purchase_order_id)
                    if repeat_queryset.exists():
                        self.message_user("单号%s重复导入" % purchase_order_id, "error")
                        n -= 1
                        obj.mistake_tag = 1
                        obj.save()
                        continue
                    purchase_order = PurchaseInfo()
                    purchase_order.purchase_order_id = purchase_order_id

                    q_supplier = ManuInfo.objects.filter(company_name=obj.supplier)
                    if q_supplier.exists():
                        supplier = q_supplier[0]
                        purchase_order.supplier = supplier
                    else:
                        self.message_user("单号%s工厂错误，查看系统是否有此工厂" % purchase_order_id, "error")
                        n -= 1
                        obj.mistake_tag = 2
                        obj.save()
                        continue
                    q_goods = GoodsInfo.objects.filter(goods_id=obj.goods_id)
                    if q_goods.exists():
                        goods = q_goods[0]
                        purchase_order.goods_name = goods
                    else:
                        self.message_user("单号%s货品错误，查看系统是否有此货品" % purchase_order_id, "error")
                        n -= 1
                        obj.mistake_tag = 3
                        obj.save()
                        continue

                    fields_list = ['order_id', 'purchase_time', 'status', 'puchaser', 'is_cancel', 'quantity', 'price',
                                   'delivery_date', 'goods_id', 'is_gift', 'is_close']

                    for k in fields_list:
                        if hasattr(obj, k):
                            setattr(purchase_order, k, getattr(obj, k))  # 更新对象属性对应键值
                    try:
                        purchase_order.creator = self.request.user.username
                        purchase_order.save()
                    except Exception as e:
                        self.message_user("单号%s递交错误：%s" % (purchase_order_id, e), "error")
                        n -= 1
                        obj.mistake_tag = 4
                        obj.save()
                        continue

                    obj.order_status = 2
                    obj.save()
                    # self.message_user("%s 审核完毕" % purchase_order_id, "info")

            self.message_user("成功提交 %(count)d %(items)s." % {"count": n, "items": model_ngettext(self.opts, n)},
                              'success')

        return None


# #####递未递交原始采购单#####递
class OriPurchaseUnhandleAdmin(object):
    list_display = ['order_id', 'mistake_tag', 'order_status', 'purchase_time', 'delivery_date', 'supplier',
                    'puchaser', 'goods_id', 'goods_name', 'quantity', 'goods_unit']
    list_filter = ['mistake_tag', 'order_status', 'purchase_time', 'mistake_tag', 'supplier', 'puchaser', 'quantity',
                   'delivery_date', 'goods_name']
    search_fields = ['order_id', 'goods_name', 'goods_id']
    actions = [PurSMAction, RejectSelectedAction]
    import_data = True

    def post(self, request, *args, **kwargs):

        file = request.FILES.get('file', None)
        if file:
            result = self.handle_upload_file(file)
            if isinstance(result, dict):
                self.message_user('导入成功数据%s条' % result['successful'], 'success')
                if result['false'] > 0:
                    self.message_user('导入失败数据%s条,主要的错误是%s' % (result['false'], result['error']), 'warning')
                if result['repeated'] > 0:
                    self.message_user('包含更新重复数据%s条' % result['repeated'], 'error')
            else:
                self.message_user('结果提示：%s' % result)
        return super(OriPurchaseUnhandleAdmin, self).post(request, args, kwargs)

    def handle_upload_file(self, _file):

        INIT_FIELDS_DIC = {
            '明细信息行号': 'detail_num',
            '单据编号': 'order_id',
            '采购日期': 'purchase_time',
            '供应商': 'supplier',
            '单据状态': 'status',
            '采购组织': 'puchaser',
            '关闭状态': 'is_cancel',
            '采购单位': 'goods_unit',
            '采购数量': 'quantity',
            '交货日期': 'delivery_date',
            '含税单价': 'price',
            '物料编码': 'goods_id',
            '物料名称': 'goods_name',
            '是否赠品': 'is_gift',
            '业务关闭': 'is_close'
        }
        ALLOWED_EXTENSIONS = ['xls', 'xlsx']
        report_dic = {"successful": 0, "discard": 0, "false": 0, "repeated": 0, "error": []}

        if '.' in _file.name and _file.name.rsplit('.')[-1] in ALLOWED_EXTENSIONS:
            with pd.ExcelFile(_file) as xls:
                df = pd.read_excel(xls, sheet_name=0)
                VERIFY_FIELD = ['单据编号', '采购日期', '供应商', '单据状态', '采购组织', '关闭状态']
                for i in VERIFY_FIELD:
                    keyword = None
                    try:
                        for j in range(len(df.loc[:, [i]])):
                            if str(df.at[j, i]) not in ['nan', 'NaN', ' ']:
                                keyword = df.at[j, i]
                            else:
                                df.at[j, i] = keyword
                    except Exception as e:
                        self.message_user('表格错误', 'error')
                        return '看下自己的表啥情况。'
                # 获取表头，对表头进行转换成数据库字段名
                columns_key = df.columns.values.tolist()
                for i in range(len(columns_key)):
                    columns_key[i] = columns_key[i].replace(' ', '').replace('=', '')

                for i in range(len(columns_key)):
                    if INIT_FIELDS_DIC.get(columns_key[i], None) is not None:
                        columns_key[i] = INIT_FIELDS_DIC.get(columns_key[i])

                # 验证一下必要的核心字段是否存在
                _ret_verify_field = OriPurchaseUnhandle.verify_mandatory(columns_key)
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
                _ret_verify_field = OriPurchaseUnhandle.verify_mandatory(columns_key)
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
            order_id = row["order_id"]
            if order_id == '合计':
                break
            # ERP导出文档添加了等于号，毙掉等于号。
            # row['purchase_time'] = datetime.datetime.strptime(row['purchase_time'], '%Y/%m/%d')
            # row['delivery_date'] = datetime.datetime.strptime(row['delivery_date'], '%Y/%m/%d %H:%M:%S')
            order = OriPurchaseUnhandle()  # 创建表格每一行为一个对象
            # for k, v in row.items():
            #     if re.match(r'^=', str(v)):
            #         row[k] = v.replace('=', '').replace('"', '')

            order_id = str(row["order_id"])
            detail_num = str(row["detail_num"])

            # 如果订单号查询，已经存在，丢弃订单，计数为重复订单
            if OriPurchaseInfo.objects.filter(order_id=order_id, detail_num=detail_num).exists():
                report_dic["repeated"] += 1
                report_dic["error"].append('%s单据重复导入货品为：%s' % (order_id, detail_num))
                continue

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

    def queryset(self):
        queryset = super(OriPurchaseUnhandleAdmin, self).queryset()
        queryset = queryset.filter(is_delete=0, order_status=1)
        return queryset

    def has_add_permission(self):
        # 禁用添加按钮
        return False


# 原始采购单
class OriPurchaseInfoAdmin(object):
    list_display = ['order_id', 'mistake_tag', 'order_status', 'purchase_time', 'delivery_date', 'supplier',
                    'puchaser', 'goods_id', 'goods_name', 'quantity', 'goods_unit']
    list_filter = ['mistake_tag', 'order_status', 'purchase_time', 'mistake_tag', 'supplier', 'puchaser', 'quantity',
                   'delivery_date', 'goods_name']
    search_fields = ['order_id', 'goods_name', 'goods_id']
    readonly_fields = ['detail_num', 'order_id', 'purchase_time', 'supplier', 'status', 'puchaser', 'is_cancel',
                       'goods_unit', 'quantity', 'delivery_date', 'price', 'goods_id', 'goods_name', 'is_gift',
                       'is_close', 'order_status', 'mistake_tag', 'creator', 'create_time', 'update_time', 'is_delete']


# 递交原始采购入库单
class OriSIAction(BaseActionView):
    action_name = "submit_si_ori"
    description = "提交选中的订单"
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
                    order_id = '{0}-{1}'.format(str(obj.order_id), str(obj.detail_num))
                    if CovertSI.objects.filter(order_id=order_id).exists():
                        self.message_user("单号%s递交重复，检查问题" % obj.order_id, "error")
                        n -= 1
                        obj.mistake_tag = 1
                        obj.save()
                        continue
                    order = CovertSI()
                    order.order_id = order_id
                    supplier = obj.supplier
                    _q_supplier = CompanyInfo.objects.filter(company_name=supplier)
                    if _q_supplier.exists():
                        order.supplier = _q_supplier[0]
                    else:
                        self.message_user("单号%s供货商非法，查看系统是否有此供货商" % obj.order_id, "error")
                        n -= 1
                        obj.mistake_tag = 2
                        obj.save()
                        continue
                    department = obj.department
                    _q_department = DepartmentInfo.objects.filter(name=department)
                    if _q_department.exists():
                        order.department = _q_department[0]
                    else:
                        self.message_user("单号%s部门非法，查看系统是否有此部门" % obj.order_id, "error")
                        n -= 1
                        obj.mistake_tag = 3
                        obj.save()
                        continue
                    goods = obj.goods_id
                    _q_goods = GoodsInfo.objects.filter(goods_id=goods)
                    if _q_goods.exists():
                        order.goods_name = _q_goods[0]
                    else:
                        self.message_user("单号%s货品非法，查看系统是否有货品" % obj.order_id, "error")
                        n -= 1
                        obj.mistake_tag = 4
                        obj.save()
                        continue
                    warehouse = obj.warehouse
                    _q_warehouse = WarehouseGeneral.objects.filter(warehouse_name=warehouse)
                    if _q_warehouse.exists():
                        order.warehouse = _q_warehouse[0]
                    else:
                        self.message_user("单号%s仓库错误，查看系统是否有此仓库" % obj.order_id, "error")
                        n -= 1
                        obj.mistake_tag = 5
                        obj.save()
                        continue
                    order.order_category = order.department.category
                    order.origin_order_category = obj.order_category
                    order.origin_order_id = obj.order_id
                    fields_list = ['order_creator', 'create_date', 'seller',
                                   'bs_category','ori_creator', 'payee', 'stockin_date',
                                   'purchaser', 'goods_id', 'quantity_receivable', 'quantity_received', 'batch_number',
                                   'expiry_date', 'produce_date', 'memorandum', 'price', ]

                    for k in fields_list:
                        if hasattr(obj, k):
                            setattr(order, k, getattr(obj, k))  # 更新对象属性对应键值
                    try:
                        order.creator = self.request.user.username
                        order.save()
                    except Exception as e:
                        self.message_user("单号%s实例保存出错：%s" % (obj.order_id, e), "error")
                        n -= 1
                        obj.mistake_tag = 6
                        obj.save()
                        continue
                    obj.order_status = 2
                    obj.mistake_tag = 0
                    obj.save()

            self.message_user("成功提交 %(count)d %(items)s." % {"count": n, "items": model_ngettext(self.opts, n)},
                              'success')

        return None


# #####未递交原始采购入库单#####
class OriStockInUnhandleAdmin(object):
    list_display = ['detail_num', 'order_id', 'mistake_tag',  'department', 'supplier', 'stockin_date', 'goods_id',
                    'goods_name', 'goods_size', 'quantity_received', 'price', 'batch_number', 'warehouse',
                    'storage', 'expiry_date', 'produce_date', 'purchase_order_id', 'multiple', 'ori_creator']

    list_filter = ['mistake_tag', 'order_status', 'ori_creator', 'supplier', 'create_date', 'department',
                   'seller', 'bs_category', 'payee', 'stockin_date', 'ori_creator',
                   'purchaser', 'goods_id', 'goods_name', 'quantity_received', 'price',
                   'batch_number', 'warehouse', 'expiry_date', 'produce_date', 'purchase_order_id', 'multiple']

    search_fields = ['order_id']
    actions = [OriSIAction, RejectSelectedAction]
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
                self.message_user('错误提示：%s' % result)
        return super(OriStockInUnhandleAdmin, self).post(request, *args, **kwargs)

    def handle_upload_file(self, _file):
        INIT_FIELDS_DIC = {
            '明细信息行号': 'detail_num',
            '单据类型': 'order_category',
            '创建人': 'ori_creator',
            '供货方': 'supplier',
            '创建日期': 'create_date',
            '结算方': 'seller',
            '业务类型': 'bs_category',
            '单据编号': 'order_id',
            '最后修改人': 'last_modifier',
            '收款方': 'payee',
            '入库日期': 'stockin_date',
            '最后修改日期': 'last_modify_time',
            '采购组织': 'purchaser',
            '收料部门': 'department',
            '物料编码': 'goods_id',
            '物料名称': 'goods_name',
            '规格型号': 'goods_size',
            '应收数量': 'quantity_receivable',
            '实收数量': 'quantity_received',
            '成本价': 'price',
            '批号': 'batch_number',
            '仓库': 'warehouse',
            '仓位': 'storage',
            '有效期至': 'expiry_date',
            '生产日期': 'produce_date',
            '源单类型': 'origin_order_category',
            '源单编号': 'origin_order_id',
            '订单单号': 'purchase_order_id',
            '主/辅换算率': 'multiple',
        }
        ALLOWED_EXTENSIONS = ['xls', 'xlsx']
        report_dic = {"successful": 0, "discard": 0, "false": 0, "repeated": 0, "error": []}

        if '.' in _file.name and _file.name.rsplit('.')[-1] in ALLOWED_EXTENSIONS:
            with pd.ExcelFile(_file) as xls:
                df = pd.read_excel(xls, sheet_name=0)
                FILTER_FIELDS = ['明细信息行号', '单据类型', '创建人', '供货方', '创建日期', '结算方', '业务类型', '单据编号', '最后修改人', '收款方',
                                 '入库日期', '最后修改日期', '收料组织', '货主', '采购组织', '单据状态', '收料部门', '物料编码', '物料名称', '规格型号', '应收数量',
                                 '实收数量', '成本价', '批号', '仓库', '仓位', '有效期至', '生产日期', '源单类型', '源单编号',
                                 '订单单号', '主/辅换算率'
                                 ]
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
                _ret_verify_field = OriStockInUnhandle.verify_mandatory(columns_key)
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
                _ret_verify_field = OriStockInUnhandle.verify_mandatory(columns_key)
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
            detail_num = row["detail_num"]
            if detail_num == '合计':
                break
            # ERP导出文档添加了等于号，毙掉等于号。
            order = OriStockInUnhandle()  # 创建表格每一行为一个对象
            # for k, v in row.items():
            #     if re.match(r'^=', str(v)):
            #         row[k] = v.replace('=', '').replace('"', '')

            order_id = str(row["order_id"])

            # 如果订单号查询，已经存在，丢弃订单，计数为重复订单
            if OriStockInInfo.objects.filter(order_id=order_id, detail_num=detail_num).exists():
                report_dic["repeated"] += 1
                report_dic["error"].append('%s单据重复导入' % order_id)
                continue

            row['create_date'] = datetime.datetime.strptime(row['create_date'], '%Y/%m/%d')
            row['stockin_date'] = datetime.datetime.strptime(row['stockin_date'], '%Y/%m/%d')
            row['last_modify_time'] = datetime.datetime.strptime(row['last_modify_time'], '%Y/%m/%d')
            try:
                row['produce_date'] = datetime.datetime.strptime(row['produce_date'], '%Y/%m/%d')
                row['expiry_date'] = datetime.datetime.strptime(row['expiry_date'], '%Y/%m/%d')
            except Exception as e:
                row['produce_date'] = row['stockin_date']
                row['expiry_date'] = row['stockin_date'] + datetime.timedelta(days=180)
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

    def queryset(self):
        queryset = super(OriStockInUnhandleAdmin, self).queryset()
        queryset = queryset.filter(is_delete=0, order_status=1)
        return queryset


# 原始采购入库单
class OriStockInInfoAdmin(object):
    list_display = ['detail_num', 'order_id', 'mistake_tag',  'department', 'supplier', 'stockin_date', 'goods_id',
                    'goods_name', 'goods_size', 'quantity_received', 'price', 'batch_number', 'warehouse',
                    'storage', 'expiry_date', 'produce_date', 'purchase_order_id', 'multiple', 'ori_creator']

    list_filter = ['mistake_tag', 'order_status', 'ori_creator', 'supplier', 'create_date', 'department',
                   'seller', 'bs_category', 'payee', 'stockin_date', 'ori_creator',
                   'purchaser', 'goods_id', 'goods_name', 'quantity_received', 'price',
                   'batch_number', 'warehouse', 'expiry_date', 'produce_date', 'purchase_order_id', 'multiple']
    readonly_fields = ['order_id', 'mistake_tag', 'order_status', 'supplier', 'create_date', 'purchaser',
                       'goods_name', 'goods_size', 'goods_unit', 'quantity_receivable', 'quantity_received',
                       'warehouse', 'origin_order_id', 'purchase_order_id','goods_id',]


# 递交原始销售出库单
class OriSOAction(BaseActionView):
    action_name = "submit_so_ori"
    description = "提交选中的订单"
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
                    order_id = '{0}-{1}'.format(str(obj.order_id), str(obj.detail_num))
                    if CovertSO.objects.filter(order_id=order_id).exists():
                        self.message_user("单号%s递交重复，检查问题" % obj.order_id, "error")
                        n -= 1
                        obj.mistake_tag = 1
                        obj.save()
                        continue
                    order = CovertSO()
                    order.order_id = order_id

                    department = obj.department
                    _q_department = DepartmentInfo.objects.filter(name=department)
                    if _q_department.exists():
                        order.department = _q_department[0]
                    else:
                        self.message_user("单号%s部门非法，查看系统是否有此部门" % obj.order_id, "error")
                        n -= 1
                        obj.mistake_tag = 2
                        obj.save()
                        continue
                    goods = obj.goods_id
                    _q_goods = GoodsInfo.objects.filter(goods_id=goods)
                    if _q_goods.exists():
                        order.goods_name = _q_goods[0]
                    else:
                        self.message_user("单号%s货品非法，查看系统是否有货品" % obj.order_id, "error")
                        n -= 1
                        obj.mistake_tag = 3
                        obj.save()
                        continue
                    warehouse = obj.warehouse
                    _q_warehouse = WarehouseGeneral.objects.filter(warehouse_name=warehouse)
                    if _q_warehouse.exists():
                        order.warehouse = _q_warehouse[0]
                    else:
                        self.message_user("单号%s仓库错误，查看系统是否有此仓库" % obj.order_id, "error")
                        n -= 1
                        obj.mistake_tag = 4
                        obj.save()
                        continue
                    order.order_category = order.department.category
                    order.origin_order_category = obj.order_category
                    order.origin_order_id = obj.order_id
                    fields_list = ['customer', 'sale_organization', 'memorandum', 'ori_creator', 'date', 'goods_id',
                                   'quantity', 'price', 'amount', 'buyer', 'address']

                    for k in fields_list:
                        if hasattr(obj, k):
                            setattr(order, k, getattr(obj, k))  # 更新对象属性对应键值
                    try:
                        order.creator = self.request.user.username
                        order.save()
                    except Exception as e:
                        self.message_user("单号%s实例保存出错：%s" % (obj.order_id, e), "error")
                        n -= 1
                        obj.mistake_tag = 5
                        obj.save()
                        continue
                    obj.order_status = 2
                    obj.mistake_tag = 0
                    obj.save()

            self.message_user("成功提交 %(count)d %(items)s." % {"count": n, "items": model_ngettext(self.opts, n)},
                              'success')

        return None


# #####未递交原始销售出库单#####
class OriStockOutUnhandleAdmin(object):
    list_display = ['order_status', 'mistake_tag', 'detail_num', 'date', 'order_id', 'customer', 'order_category',
                    'sale_organization', 'department', 'memorandum', 'buyer', 'address', 'ori_creator',
                    'goods_id', 'goods_name', 'goods_size', 'quantity', 'warehouse', 'price', 'amount', 'package_size']

    list_filter = ['mistake_tag', 'order_status', 'date', 'customer', 'department', 'memorandum', 'ori_creator',
                   'goods_id', 'goods_name', 'quantity', 'warehouse', 'price', 'amount', 'package_size']

    search_fields = ['order_id',]
    actions = [OriSOAction, RejectSelectedAction]
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
                self.message_user('错误提示：%s' % result)
        return super(OriStockOutUnhandleAdmin, self).post(request, *args, **kwargs)

    def handle_upload_file(self, _file):
        INIT_FIELDS_DIC = {
            '明细信息行号': 'detail_num',
            '日期': 'date',
            '单据编号': 'order_id',
            '客户': 'customer',
            '单据状态': 'ori_order_status',
            '单据类型': 'order_category',
            '销售组织': 'sale_organization',
            '销售部门': 'department',
            '备注': 'memorandum',
            '收货方': 'buyer',
            '收货方地址': 'address',
            '创建人': 'ori_creator',
            '物料编码': 'goods_id',
            '物料名称': 'goods_name',
            '规格型号': 'goods_size',
            '实发数量': 'quantity',
            '仓库': 'warehouse',
            '含税单价': 'price',
            '价税合计': 'amount',
            '主/辅换算率': 'package_size',
            }
        ALLOWED_EXTENSIONS = ['xls', 'xlsx']
        report_dic = {"successful": 0, "discard": 0, "false": 0, "repeated": 0, "error": []}

        if '.' in _file.name and _file.name.rsplit('.')[-1] in ALLOWED_EXTENSIONS:
            with pd.ExcelFile(_file) as xls:
                df = pd.read_excel(xls, sheet_name=0)
                FILTER_FIELDS = ['明细信息行号', '日期', '单据编号', '客户', '单据状态', '单据类型', '销售组织', '销售部门', '备注', '收货方', '收货方地址',
                                 '创建人', '物料编码', '物料名称', '规格型号', '实发数量', '仓库', '含税单价', '价税合计', '主/辅换算率']

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
                _ret_verify_field = OriStockOutUnhandle.verify_mandatory(columns_key)
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
                _ret_verify_field = OriStockOutUnhandle.verify_mandatory(columns_key)
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
            detail_num = row["detail_num"]
            if detail_num == '合计':
                break

            order = OriStockOutUnhandle()  # 创建表格每一行为一个对象
            # for k, v in row.items():
            #     if re.match(r'^=', str(v)):
            #         row[k] = v.replace('=', '').replace('"', '')

            order_id = str(row["order_id"])

            detail_num = row['detail_num']

            # 如果订单号查询，已经存在，丢弃订单，计数为重复订单
            if OriStockOut.objects.filter(order_id=order_id, detail_num=detail_num).exists():
                report_dic["repeated"] += 1
                report_dic["error"].append('%s单据重复导入' % order_id)
                continue
            if str(row['price']) in ['nan', 'NaN']:
                row['price'] = 0
                row['amount'] = 0
            row['date'] = datetime.datetime.strptime(row['date'], '%Y/%m/%d')

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

    def queryset(self):
        queryset = super(OriStockOutUnhandleAdmin, self).queryset()
        queryset = queryset.filter(is_delete=0, order_status=1)
        return queryset

    def has_add_permission(self):
        # 禁用添加按钮
        return False


# 原始销售出库单
class OriStockOutAdmin(object):
    list_display = ['detail_num', 'order_id', 'mistake_tag', 'order_status', 'date', 'customer', 'ori_order_status',
                    'sale_organization', 'department', 'memorandum', 'buyer', 'address', 'creator',
                    'goods_id', 'goods_name', 'goods_size', 'quantity', 'warehouse', 'price',
                    'amount', 'package_size']
    list_filter = ['mistake_tag', 'order_status', 'date', 'customer', 'department', 'buyer', 'address', 'ori_creator',
                   'goods_id', 'goods_name', 'quantity', 'warehouse', 'price',
                   'amount', 'package_size', 'creator', 'create_time', 'memorandum']

    search_fields = ['order_id']


# 递交原始其他出库单
class OriNSSOAction(BaseActionView):
    action_name = "submit_nsso_ori"
    description = "提交选中的订单"
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
                    order_id = '{0}-{1}'.format(str(obj.order_id), str(obj.detail_num))
                    if CovertSO.objects.filter(order_id=order_id).exists():
                        self.message_user("单号%s递交重复，检查问题" % obj.order_id, "error")
                        n -= 1
                        obj.mistake_tag = 1
                        obj.save()
                        continue
                    order = CovertSO()
                    order.order_id = order_id

                    department = obj.department
                    _q_department = DepartmentInfo.objects.filter(name=department)
                    if _q_department.exists():
                        order.department = _q_department[0]
                    else:
                        self.message_user("单号%s部门非法，查看系统是否有此部门" % obj.order_id, "error")
                        n -= 1
                        obj.mistake_tag = 2
                        obj.save()
                        continue
                    goods = obj.goods_id
                    _q_goods = GoodsInfo.objects.filter(goods_id=goods)
                    if _q_goods.exists():
                        order.goods_name = _q_goods[0]
                    else:
                        self.message_user("单号%s货品非法，查看系统是否有货品" % obj.order_id, "error")
                        n -= 1
                        obj.mistake_tag = 3
                        obj.save()
                        continue
                    warehouse = obj.warehouse
                    _q_warehouse = WarehouseGeneral.objects.filter(warehouse_name=warehouse)
                    if _q_warehouse.exists():
                        order.warehouse = _q_warehouse[0]
                    else:
                        self.message_user("单号%s仓库错误，查看系统是否有此仓库" % obj.order_id, "error")
                        n -= 1
                        obj.mistake_tag = 4
                        obj.save()
                        continue
                    if obj.customer is None:
                        obj.customer = '零售顾客'
                    order.order_category = order.department.category
                    order.origin_order_category = obj.order_category
                    order.origin_order_id = obj.order_id
                    order.price = 0
                    order.amount = 0
                    order.memorandum = '店号：{0}-出库类型：{1}-备注{2}'.format(str(obj.store_id), str(obj.out_category), str(obj.memorandum))
                    if len(order.memorandum) > 300:
                        order.memorandum = order.memorandum[:300]
                    fields_list = ['customer', 'ori_creator', 'date', 'goods_id', 'quantity', 'buyer', 'address']

                    for k in fields_list:
                        if hasattr(obj, k):
                            setattr(order, k, getattr(obj, k))  # 更新对象属性对应键值
                    try:
                        order.creator = self.request.user.username
                        order.save()
                    except Exception as e:
                        self.message_user("单号%s实例保存出错：%s" % (obj.order_id, e), "error")
                        n -= 1
                        obj.mistake_tag = 5
                        obj.save()
                        continue
                    obj.order_status = 2
                    obj.mistake_tag = 0
                    obj.save()

            self.message_user("成功提交 %(count)d %(items)s." % {"count": n, "items": model_ngettext(self.opts, n)},
                              'success')

        return None


# #####未递交原始其他出库单#####
class OriNSSOUnhandleAdmin(object):
    list_display = ['order_status', 'mistake_tag', 'detail_num', 'order_category', 'customer', 'department', 'owner',
                    'order_id', 'date', 'ori_creator', 'goods_id', 'goods_name', 'goods_size',
                    'quantity', 'warehouse', 'out_category']

    list_filter = ['mistake_tag', 'order_status', 'customer', 'department', 'date', 'ori_creator',
                   'goods_id', 'goods_name', 'quantity', 'warehouse', 'out_category']

    search_fields = ['order_id', ]
    actions = [OriNSSOAction, RejectSelectedAction]
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
                self.message_user('错误提示：%s' % result)
        return super(OriNSSOUnhandleAdmin, self).post(request, *args, **kwargs)

    def handle_upload_file(self, _file):
        INIT_FIELDS_DIC = {
            '明细信息行号': 'detail_num',
            '单据类型': 'order_category',
            '客户': 'customer',
            '领料部门': 'department',
            '货主': 'owner',
            '备注': 'memorandum',
            '单据编号': 'order_id',
            '创建人': 'ori_creator',
            '日期': 'date',
            '物料编码': 'goods_id',
            '物料名称': 'goods_name',
            '规格型号': 'goods_size',
            '实发数量': 'quantity',
            '发货仓库': 'warehouse',
            '店号': 'store_id',
            '收货人': 'buyer',
            '联系电话': 'smartphone',
            '收货地址': 'address',
            '出库类型': 'out_category'
        }
        ALLOWED_EXTENSIONS = ['xls', 'xlsx']
        report_dic = {"successful": 0, "discard": 0, "false": 0, "repeated": 0, "error": []}

        if '.' in _file.name and _file.name.rsplit('.')[-1] in ALLOWED_EXTENSIONS:
            with pd.ExcelFile(_file) as xls:
                df = pd.read_excel(xls, sheet_name=0)
                FILTER_FIELDS = ['明细信息行号', '单据类型', '客户', '领料部门', '货主', '备注', '单据编号', '日期', '创建人', '创建日期', '物料编码',
                                 '物料名称', '规格型号', '实发数量', '发货仓库', '店号', '收货人', '联系电话', '收货地址', '出库类型']

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
                _ret_verify_field = OriNSSOUnhandle.verify_mandatory(columns_key)
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
                _ret_verify_field = OriNSSOUnhandle.verify_mandatory(columns_key)
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
            detail_num = row["detail_num"]
            if detail_num == '合计':
                break

            order = OriNSSOUnhandle()  # 创建表格每一行为一个对象
            for k, v in row.items():
                if re.match(r'^=', str(v)):
                    row[k] = v.replace('=', '').replace('"', '')

            order_id = str(row["order_id"])
            row['order_id'] = order_id
            detail_num = row['detail_num']

            # 如果订单号查询，已经存在，丢弃订单，计数为重复订单
            if OriNSStockout.objects.filter(order_id=order_id, detail_num=detail_num).exists():
                report_dic["repeated"] += 1
                report_dic["error"].append('%s单据重复导入' % order_id)
                continue

            row['date'] = datetime.datetime.strptime(row['date'], '%Y/%m/%d')

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

    def queryset(self):
        queryset = super(OriNSSOUnhandleAdmin, self).queryset()
        queryset = queryset.filter(is_delete=0, order_status=1)
        return queryset

    def has_add_permission(self):
        # 禁用添加按钮
        return False


# 原始其他出库单
class OriNSStockoutAdmin(object):
    list_display = ['order_status', 'mistake_tag', 'detail_num', 'order_category', 'customer', 'department', 'owner',
                    'order_id', 'date', 'ori_creator', 'goods_id', 'goods_name', 'goods_size',
                    'quantity', 'warehouse', 'out_category']

    list_filter = ['mistake_tag', 'order_status', 'customer', 'department', 'date', 'ori_creator',
                   'goods_id', 'goods_name', 'quantity', 'warehouse', 'out_category']

    search_fields = ['order_id', ]

    def has_add_permission(self):
        # 禁用添加按钮
        return False


# 递交原始其他入库单
class OriNPSIAction(BaseActionView):
    action_name = "submit_npsi_ori"
    description = "提交选中的订单"
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
                    order_id = '{0}-{1}'.format(str(obj.order_id), str(obj.detail_num))
                    if CovertSI.objects.filter(order_id=order_id).exists():
                        self.message_user("单号%s递交重复，检查问题" % obj.order_id, "error")
                        n -= 1
                        obj.mistake_tag = 1
                        obj.save()
                        continue
                    order = CovertSI()
                    order.order_id = order_id
                    supplier = obj.owner
                    order.payee = supplier
                    order.purchaser = supplier
                    _q_supplier = CompanyInfo.objects.filter(company_name=supplier)
                    if _q_supplier.exists():
                        order.supplier = _q_supplier[0]
                    else:
                        self.message_user("单号%s供货商非法，查看系统是否有此供货商" % obj.order_id, "error")
                        n -= 1
                        obj.mistake_tag = 2
                        obj.save()
                        continue
                    department = obj.department
                    _q_department = DepartmentInfo.objects.filter(name=department)
                    if _q_department.exists():
                        order.department = _q_department[0]
                    else:
                        self.message_user("单号%s部门非法，查看系统是否有此部门" % obj.order_id, "error")
                        n -= 1
                        obj.mistake_tag = 3
                        obj.save()
                        continue
                    goods = obj.goods_id
                    _q_goods = GoodsInfo.objects.filter(goods_id=goods)
                    if _q_goods.exists():
                        order.goods_name = _q_goods[0]
                    else:
                        self.message_user("单号%s货品非法，查看系统是否有货品" % obj.order_id, "error")
                        n -= 1
                        obj.mistake_tag = 4
                        obj.save()
                        continue
                    warehouse = obj.warehouse
                    _q_warehouse = WarehouseGeneral.objects.filter(warehouse_name=warehouse)
                    if _q_warehouse.exists():
                        order.warehouse = _q_warehouse[0]
                    else:
                        self.message_user("单号%s仓库错误，查看系统是否有此仓库" % obj.order_id, "error")
                        n -= 1
                        obj.mistake_tag = 5
                        obj.save()
                        continue
                    order.memorandum = '入库类型:{0}-备注:{1}'.format(obj.in_category, obj.memorandum)
                    if len(str(order.memorandum)) > 300:
                        order.memorandum = order.memorandum[:300]
                    order.price = 0

                    order.quantity_received = obj.quantity
                    order.quantity_receivable = obj.quantity
                    order.order_category = order.department.category
                    order.origin_order_category = obj.order_category
                    order.create_date = obj.date
                    order.stockin_date = obj.date
                    order.origin_order_id = obj.order_id


                    fields_list = ['ori_creator', 'goods_id', 'batch_number', 'expiry_date', 'produce_date']

                    for k in fields_list:
                        if hasattr(obj, k):
                            setattr(order, k, getattr(obj, k))  # 更新对象属性对应键值
                    try:
                        order.creator = self.request.user.username
                        order.save()
                    except Exception as e:
                        self.message_user("单号%s实例保存出错：%s" % (obj.order_id, e), "error")
                        n -= 1
                        obj.mistake_tag = 6
                        obj.save()
                        continue
                    obj.order_status = 2
                    obj.mistake_tag = 0
                    obj.save()

            self.message_user("成功提交 %(count)d %(items)s." % {"count": n, "items": model_ngettext(self.opts, n)},
                              'success')

        return None


# #####未递交原始其他入库单#####
class OriNPSIUnhandleAdmin(object):
    list_display = ['order_status', 'mistake_tag', 'detail_num', 'order_id', 'order_category', 'date', 'department',
                    'ori_creator', 'owner', 'memorandum', 'goods_id', 'goods_name', 'goods_size', 'quantity',
                    'warehouse', 'batch_number', 'produce_date', 'expiry_date', 'in_category']

    list_filter = ['mistake_tag', 'order_status', 'date', 'department', 'ori_creator', 'memorandum', 'goods_id',
                   'goods_name', 'quantity', 'warehouse', 'batch_number', 'produce_date', 'expiry_date', 'in_category']

    search_fields = ['order_id', ]
    actions = [OriNPSIAction, RejectSelectedAction]
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
                self.message_user('错误提示：%s' % result)
        return super(OriNPSIUnhandleAdmin, self).post(request, *args, **kwargs)

    def handle_upload_file(self, _file):
        INIT_FIELDS_DIC = {
            '明细信息行号': 'detail_num',
            '单据编号': 'order_id',
            '单据类型': 'order_category',
            '日期': 'date',
            '部门': 'department',
            '创建人': 'ori_creator',
            '货主': 'owner',
            '备注': 'memorandum',
            '物料编码': 'goods_id',
            '物料名称': 'goods_name',
            '规格型号': 'goods_size',
            '实收数量': 'quantity',
            '收货仓库': 'warehouse',
            '批号': 'batch_number',
            '生产日期': 'produce_date',
            '有效期至': 'expiry_date',
            '入库类型': 'in_category'
        }
        ALLOWED_EXTENSIONS = ['xls', 'xlsx']
        report_dic = {"successful": 0, "discard": 0, "false": 0, "repeated": 0, "error": []}

        if '.' in _file.name and _file.name.rsplit('.')[-1] in ALLOWED_EXTENSIONS:
            with pd.ExcelFile(_file) as xls:
                df = pd.read_excel(xls, sheet_name=0)
                FILTER_FIELDS = ['明细信息行号', '单据编号', '单据类型', '日期', '部门', '创建人', '货主', '备注', '物料编码',
                                 '物料名称', '规格型号', '实收数量', '收货仓库', '批号', '生产日期', '有效期至', '入库类型']

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
                _ret_verify_field = OriNPSIUnhandle.verify_mandatory(columns_key)
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
                _ret_verify_field = OriNPSIUnhandle.verify_mandatory(columns_key)
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
            detail_num = row["detail_num"]
            if detail_num == '合计':
                break

            order = OriNPSIUnhandle()  # 创建表格每一行为一个对象
            for k, v in row.items():
                if re.match(r'^=', str(v)):
                    row[k] = v.replace('=', '').replace('"', '')

            order_id = str(row["order_id"])
            row['order_id'] = order_id
            detail_num = row['detail_num']

            # 如果订单号查询，已经存在，丢弃订单，计数为重复订单
            if OriNPStockIn.objects.filter(order_id=order_id, detail_num=detail_num).exists():
                report_dic["repeated"] += 1
                report_dic["error"].append('%s单据重复导入' % order_id)
                continue

            row['date'] = datetime.datetime.strptime(row['date'], '%Y/%m/%d')
            row['produce_date'] = datetime.datetime.strptime(row['produce_date'], '%Y/%m/%d')
            row['expiry_date'] = datetime.datetime.strptime(row['expiry_date'], '%Y/%m/%d')

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

    def queryset(self):
        queryset = super(OriNPSIUnhandleAdmin, self).queryset()
        queryset = queryset.filter(is_delete=0, order_status=1)
        return queryset

    def has_add_permission(self):
        # 禁用添加按钮
        return False


# 原始其他入库单
class OriNPStockInAdmin(object):
    list_display = ['order_status', 'mistake_tag', 'detail_num', 'order_id', 'order_category', 'date', 'department',
                    'ori_creator', 'owner', 'memorandum', 'goods_id', 'goods_name', 'goods_size', 'quantity',
                    'warehouse', 'batch_number', 'produce_date', 'expiry_date', 'in_category']

    list_filter = ['mistake_tag', 'order_status', 'date', 'department', 'ori_creator', 'memorandum', 'goods_id',
                   'goods_name', 'quantity', 'warehouse', 'batch_number', 'produce_date', 'expiry_date', 'in_category']

    search_fields = ['order_id', ]

    def has_add_permission(self):
        # 禁用添加按钮
        return False


# 递交原始销售退货单
class OriRefundAction(BaseActionView):
    action_name = "submit_refund_ori"
    description = "提交选中的订单"
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
                    order_id = '{0}-{1}'.format(str(obj.order_id), str(obj.detail_num))
                    if CovertSI.objects.filter(order_id=order_id).exists():
                        self.message_user("单号%s递交重复，检查问题" % obj.order_id, "error")
                        n -= 1
                        obj.mistake_tag = 1
                        obj.save()
                        continue
                    order = CovertSI()
                    order.order_id = order_id
                    supplier = '退货中心'
                    order.payee = supplier
                    order.purchaser = supplier
                    _q_supplier = CompanyInfo.objects.filter(company_name=supplier)
                    if _q_supplier.exists():
                        order.supplier = _q_supplier[0]
                    else:
                        self.message_user("单号%s供货商非法，查看系统是否有此供货商" % obj.order_id, "error")
                        n -= 1
                        obj.mistake_tag = 2
                        obj.save()
                        continue
                    department = obj.department
                    _q_department = DepartmentInfo.objects.filter(name=department)
                    if _q_department.exists():
                        order.department = _q_department[0]
                    else:
                        self.message_user("单号%s部门非法，查看系统是否有此部门" % obj.order_id, "error")
                        n -= 1
                        obj.mistake_tag = 3
                        obj.save()
                        continue
                    goods = obj.goods_id
                    _q_goods = GoodsInfo.objects.filter(goods_id=goods)
                    if _q_goods.exists():
                        order.goods_name = _q_goods[0]
                    else:
                        self.message_user("单号%s货品非法，查看系统是否有货品" % obj.order_id, "error")
                        n -= 1
                        obj.mistake_tag = 4
                        obj.save()
                        continue
                    warehouse = obj.warehouse
                    _q_warehouse = WarehouseGeneral.objects.filter(warehouse_name=warehouse)
                    if _q_warehouse.exists():
                        order.warehouse = _q_warehouse[0]
                    else:
                        self.message_user("单号%s仓库错误，查看系统是否有此仓库" % obj.order_id, "error")
                        n -= 1
                        obj.mistake_tag = 5
                        obj.save()
                        continue
                    order.memorandum = '退货客户:{0}-退货单号：{1}-备注:{2}'.format(obj.customer, obj.refund_information, obj.memorandum)
                    if len(str(order.memorandum)) > 300:
                        order.memorandum = order.memorandum[:300]
                    order.price = 0

                    order.quantity_received = obj.quantity
                    order.quantity_receivable = obj.quantity
                    order.order_category = order.department.category
                    order.origin_order_category = obj.order_category
                    order.create_date = obj.date
                    order.stockin_date = obj.refund_date
                    order.origin_order_id = obj.order_id

                    fields_list = ['ori_creator', 'goods_id', 'batch_number', 'expiry_date', 'produce_date', 'price']

                    for k in fields_list:
                        if hasattr(obj, k):
                            setattr(order, k, getattr(obj, k))  # 更新对象属性对应键值
                    try:
                        order.creator = self.request.user.username
                        order.save()
                    except Exception as e:
                        self.message_user("单号%s实例保存出错：%s" % (obj.order_id, e), "error")
                        n -= 1
                        obj.mistake_tag = 6
                        obj.save()
                        continue
                    obj.order_status = 2
                    obj.mistake_tag = 0
                    obj.save()

            self.message_user("成功提交 %(count)d %(items)s." % {"count": n, "items": model_ngettext(self.opts, n)},
                              'success')

        return None


# #####未递交原始销售退货单#####
class OriRefundUnhandleAdmin(object):
    list_display = ['order_status', 'mistake_tag', 'detail_num', 'order_category', 'date', 'order_id', 'customer', 'buyer',
                    'ori_creator', 'goods_id', 'goods_name', 'goods_size', 'quantity', 'refund_date', 'warehouse',
                    'batch_number', 'produce_date', 'expiry_date', 'price', 'amount', 'refund_information']

    list_filter = ['mistake_tag', 'order_status', 'date', 'order_id', 'customer', 'buyer', 'ori_creator', 'goods_id',
                   'goods_name', 'quantity', 'refund_date', 'warehouse', 'batch_number', 'produce_date', 'expiry_date',
                   'price', 'amount', 'refund_information']

    search_fields = ['order_id', ]
    actions = [OriRefundAction, RejectSelectedAction]
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
                self.message_user('错误提示：%s' % result)
        return super(OriRefundUnhandleAdmin, self).post(request, *args, **kwargs)

    def handle_upload_file(self, _file):
        INIT_FIELDS_DIC = {
            '明细信息行号': 'detail_num',
            '单据类型': 'order_category',
            '日期': 'date',
            '单据编号': 'order_id',
            '销售部门': 'department',
            '退货客户': 'customer',
            '备注': 'memorandum',
            '收货方': 'buyer',
            '创建人': 'ori_creator',
            '物料编码': 'goods_id',
            '物料名称': 'goods_name',
            '规格型号': 'goods_size',
            '实退数量': 'quantity',
            '退货日期': 'refund_date',
            '仓库': 'warehouse',
            '批号': 'batch_num',
            '生产日期': 'produce_date',
            '有效期至': 'expiry_date',
            '含税单价': 'price',
            '价税合计': 'amount',
            '货主': 'owner',
            '退货单号': 'refund_information'
        }
        ALLOWED_EXTENSIONS = ['xls', 'xlsx']
        report_dic = {"successful": 0, "discard": 0, "false": 0, "repeated": 0, "error": []}

        if '.' in _file.name and _file.name.rsplit('.')[-1] in ALLOWED_EXTENSIONS:
            with pd.ExcelFile(_file) as xls:
                df = pd.read_excel(xls, sheet_name=0)
                FILTER_FIELDS = ['明细信息行号', '单据类型', '日期', '单据编号', '销售部门', '退货客户', '备注', '收货方', '创建人', '物料编码', '物料名称',
                                 '规格型号', '实退数量', '退货日期', '仓库', '批号', '生产日期', '有效期至', '含税单价', '价税合计', '货主', '退货单号']

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
                _ret_verify_field = OriRefundUnhandle.verify_mandatory(columns_key)
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
                _ret_verify_field = OriRefundUnhandle.verify_mandatory(columns_key)
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
            detail_num = row["detail_num"]
            if detail_num == '合计':
                break

            order = OriRefundUnhandle()  # 创建表格每一行为一个对象
            for k, v in row.items():
                if re.match(r'^=', str(v)):
                    row[k] = v.replace('=', '').replace('"', '')

            order_id = str(row["order_id"])
            row['order_id'] = order_id
            detail_num = row['detail_num']

            # 如果订单号查询，已经存在，丢弃订单，计数为重复订单
            if OriRefund.objects.filter(order_id=order_id, detail_num=detail_num).exists():
                report_dic["repeated"] += 1
                report_dic["error"].append('%s单据重复导入' % order_id)
                continue

            row['date'] = datetime.datetime.strptime(row['date'], '%Y/%m/%d')
            row['refund_date'] = datetime.datetime.strptime(row['refund_date'].split(' ')[0], '%Y/%m/%d')
            try:
                row['produce_date'] = datetime.datetime.strptime(row['produce_date'], '%Y/%m/%d')
                row['expiry_date'] = datetime.datetime.strptime(row['expiry_date'], '%Y/%m/%d')
            except Exception as e:
                row['produce_date'] = row['date']
                row['expiry_date'] = row['date'] + datetime.timedelta(days=180)

            if str(row['price']) in ['nan', 'NaN']:
                row['price'] = 0
                row['amount'] = 0

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

    def queryset(self):
        queryset = super(OriRefundUnhandleAdmin, self).queryset()
        queryset = queryset.filter(is_delete=0, order_status=1)
        return queryset

    def has_add_permission(self):
        # 禁用添加按钮
        return False


# 原始销售退货单
class OriRefundAdmin(object):
    list_display = ['order_status', 'mistake_tag', 'detail_num', 'order_category', 'date', 'order_id', 'customer', 'buyer',
                    'ori_creator', 'goods_id', 'goods_name', 'goods_size', 'quantity', 'refund_date', 'warehouse',
                    'batch_number', 'produce_date', 'expiry_date', 'price', 'amount', 'refund_information']

    list_filter = ['mistake_tag', 'order_status', 'date', 'order_id', 'customer', 'buyer', 'ori_creator', 'goods_id',
                   'goods_name', 'quantity', 'refund_date', 'warehouse', 'batch_number', 'produce_date', 'expiry_date',
                   'price', 'amount', 'refund_information']

    search_fields = ['order_id', ]

    def has_add_permission(self):
        # 禁用添加按钮
        return False


# 递交原始采购退料单
class OriPRAction(BaseActionView):
    action_name = "submit_pr_ori"
    description = "提交选中的订单"
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
                    order_id = '{0}-{1}'.format(str(obj.order_id), str(obj.detail_num))
                    if CovertSO.objects.filter(order_id=order_id).exists():
                        self.message_user("单号%s递交重复，检查问题" % obj.order_id, "error")
                        n -= 1
                        obj.mistake_tag = 1
                        obj.save()
                        continue
                    order = CovertSO()
                    order.order_id = order_id
                    order.customer = obj.owner

                    department = obj.department
                    _q_department = DepartmentInfo.objects.filter(name=department)
                    if _q_department.exists():
                        order.department = _q_department[0]
                    else:
                        self.message_user("单号%s部门非法，查看系统是否有此部门" % obj.order_id, "error")
                        n -= 1
                        obj.mistake_tag = 2
                        obj.save()
                        continue
                    goods = obj.goods_id
                    _q_goods = GoodsInfo.objects.filter(goods_id=goods)
                    if _q_goods.exists():
                        order.goods_name = _q_goods[0]
                    else:
                        self.message_user("单号%s货品非法，查看系统是否有货品" % obj.order_id, "error")
                        n -= 1
                        obj.mistake_tag = 3
                        obj.save()
                        continue
                    warehouse = obj.warehouse
                    _q_warehouse = WarehouseGeneral.objects.filter(warehouse_name=warehouse)
                    if _q_warehouse.exists():
                        order.warehouse = _q_warehouse[0]
                    else:
                        self.message_user("单号%s仓库错误，查看系统是否有此仓库" % obj.order_id, "error")
                        n -= 1
                        obj.mistake_tag = 4
                        obj.save()
                        continue
                    order.memorandum = '备注:{0}-物料说明：{1}'.format(obj.memorandum, obj.goods_memo)
                    if len(str(order.memorandum)) > 300:
                        order.memorandum = order.memorandum[:300]
                    order.order_category = order.department.category
                    order.origin_order_category = obj.order_category
                    order.origin_order_id = obj.order_id
                    fields_list = ['ori_creator', 'goods_id', 'batch_num', 'price', 'date', 'quantity', 'amount']

                    for k in fields_list:
                        if hasattr(obj, k):
                            setattr(order, k, getattr(obj, k))  # 更新对象属性对应键值
                    try:
                        order.creator = self.request.user.username
                        order.save()
                    except Exception as e:
                        self.message_user("单号%s实例保存出错：%s" % (obj.order_id, e), "error")
                        n -= 1
                        obj.mistake_tag = 5
                        obj.save()
                        continue
                    obj.order_status = 2
                    obj.mistake_tag = 0
                    obj.save()

            self.message_user("成功提交 %(count)d %(items)s." % {"count": n, "items": model_ngettext(self.opts, n)},
                              'success')

        return None


# #####未递交原始采购退料单#####
class OriPRUnhandleAdmin(object):
    list_display = ['order_status', 'mistake_tag', 'detail_num', 'order_category', 'ori_creator', 'order_id', 'date', 'owner',
                    'department', 'goods_id', 'goods_name', 'goods_memo', 'batch_num', 'quantity', 'warehouse',
                    'memorandum', 'price', 'amount']

    list_filter = ['mistake_tag', 'order_status', 'ori_creator', 'date', 'department', 'goods_id', 'goods_name',
                   'goods_memo', 'batch_num', 'quantity', 'warehouse', 'memorandum', 'price', 'amount']

    search_fields = ['order_id', ]
    actions = [OriPRAction, RejectSelectedAction]
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
                self.message_user('错误提示：%s' % result)
        return super(OriPRUnhandleAdmin, self).post(request, *args, **kwargs)

    def handle_upload_file(self, _file):
        INIT_FIELDS_DIC = {
            '明细信息行号': 'detail_num',
            '单据类型': 'order_category',
            '创建人': 'ori_creator',
            '单据编号': 'order_id',
            '退料日期': 'date',
            '货主': 'owner',
            '退料部门': 'department',
            '物料编码': 'goods_id',
            '物料名称': 'goods_name',
            '物料说明': 'goods_memo',
            '批号': 'batch_num',
            '实退数量': 'quantity',
            '仓库': 'warehouse',
            '备注': 'memorandum',
            '单价': 'price',
            '价税合计': 'amount',
        }
        ALLOWED_EXTENSIONS = ['xls', 'xlsx']
        report_dic = {"successful": 0, "discard": 0, "false": 0, "repeated": 0, "error": []}

        if '.' in _file.name and _file.name.rsplit('.')[-1] in ALLOWED_EXTENSIONS:
            with pd.ExcelFile(_file) as xls:
                df = pd.read_excel(xls, sheet_name=0)
                FILTER_FIELDS = ['明细信息行号', '单据类型', '创建人', '单据编号', '退料日期', '货主', '退料部门', '物料编码',
                                 '物料名称', '物料说明', '批号', '实退数量', '仓库', '备注', '单价', '价税合计']

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
                _ret_verify_field = OriPRUnhandle.verify_mandatory(columns_key)
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
                _ret_verify_field = OriPRUnhandle.verify_mandatory(columns_key)
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
            detail_num = row["detail_num"]
            if detail_num == '合计':
                break

            order = OriPRUnhandle()  # 创建表格每一行为一个对象
            for k, v in row.items():
                if re.match(r'^=', str(v)):
                    row[k] = v.replace('=', '').replace('"', '')

            order_id = str(row["order_id"])
            row['order_id'] = order_id
            detail_num = row['detail_num']

            # 如果订单号查询，已经存在，丢弃订单，计数为重复订单
            if OriPurRefund.objects.filter(order_id=order_id, detail_num=detail_num).exists():
                report_dic["repeated"] += 1
                report_dic["error"].append('%s单据重复导入' % order_id)
                continue

            row['date'] = datetime.datetime.strptime(row['date'], '%Y/%m/%d')

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

    def queryset(self):
        queryset = super(OriPRUnhandleAdmin, self).queryset()
        queryset = queryset.filter(is_delete=0, order_status=1)
        return queryset

    def has_add_permission(self):
        # 禁用添加按钮
        return False


# 原始采购退料单
class OriPurRefundAdmin(object):
    list_display = ['order_status', 'mistake_tag', 'detail_num', 'order_category', 'ori_creator', 'order_id', 'date', 'owner',
                    'department', 'goods_id', 'goods_name', 'goods_memo', 'batch_num', 'quantity', 'warehouse',
                    'memorandum', 'price', 'amount']

    list_filter = ['mistake_tag', 'order_status', 'ori_creator', 'date', 'department', 'goods_id', 'goods_name',
                   'goods_memo', 'batch_num', 'quantity', 'warehouse', 'memorandum', 'price', 'amount']

    search_fields = ['order_id', ]

    def has_add_permission(self):
        # 禁用添加按钮
        return False


# 递交原始直接调拨单
class OriAllocationAction(BaseActionView):
    action_name = "submit_allocation_ori"
    description = "提交选中的订单"
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
                    si_order_id = '{0}-{1}-I'.format(str(obj.order_id), str(obj.detail_num))
                    so_order_id = '{0}-{1}-O'.format(str(obj.order_id), str(obj.detail_num))
                    if CovertSI.objects.filter(order_id=si_order_id).exists():
                        self.message_user("单号%s递交重复，检查问题" % obj.order_id, "error")
                        n -= 1
                        obj.mistake_tag = 1
                        obj.save()
                        continue
                    elif CovertSO.objects.filter(order_id=so_order_id).exists():
                        self.message_user("单号%s递交重复，检查问题" % obj.order_id, "error")
                        n -= 1
                        obj.mistake_tag = 1
                        obj.save()
                        continue
                    so_order = CovertSO()
                    si_order = CovertSI()
                    so_order.order_id = so_order_id
                    si_order.order_id = si_order_id
                    supplier = obj.trans_out
                    si_order.payee = supplier
                    si_order.purchaser = supplier
                    _q_supplier = CompanyInfo.objects.filter(company_name=supplier)
                    if _q_supplier.exists():
                        si_order.supplier = _q_supplier[0]
                        so_order.customer = _q_supplier[0].company_name
                    else:
                        self.message_user("单号%s供货商非法，查看系统是否有此供货商" % obj.order_id, "error")
                        n -= 1
                        obj.mistake_tag = 2
                        obj.save()
                        continue
                    department = obj.department
                    _q_department = DepartmentInfo.objects.filter(name=department)
                    so_order.department = DepartmentInfo.objects.filter(name='物流部')[0]
                    if _q_department.exists():
                        si_order.department = _q_department[0]
                    else:
                        self.message_user("单号%s部门非法，查看系统是否有此部门" % obj.order_id, "error")
                        n -= 1
                        obj.mistake_tag = 3
                        obj.save()
                        continue
                    goods = obj.goods_id
                    _q_goods = GoodsInfo.objects.filter(goods_id=goods)
                    if _q_goods.exists():
                        si_order.goods_name = _q_goods[0]
                        so_order.goods_name = _q_goods[0]
                    else:
                        self.message_user("单号%s货品非法，查看系统是否有货品" % obj.order_id, "error")
                        n -= 1
                        obj.mistake_tag = 4
                        obj.save()
                        continue

                    si_warehouse = obj.warehouse_in
                    _q_si_warehouse = WarehouseGeneral.objects.filter(warehouse_name=si_warehouse)
                    if _q_si_warehouse.exists():
                        si_order.warehouse = _q_si_warehouse[0]
                    else:
                        self.message_user("单号%s入库仓库错误，查看系统是否有此仓库" % obj.order_id, "error")
                        n -= 1
                        obj.mistake_tag = 5
                        obj.save()
                        continue

                    so_warehouse = obj.warehouse_out
                    _q_so_warehouse = WarehouseGeneral.objects.filter(warehouse_name=so_warehouse)
                    if _q_so_warehouse.exists():
                        so_order.warehouse = _q_so_warehouse[0]
                    else:
                        self.message_user("单号%s出库仓库错误，查看系统是否有此仓库" % obj.order_id, "error")
                        n -= 1
                        obj.mistake_tag = 5
                        obj.save()
                        continue

                    so_order.price = 0
                    so_order.amount = 0
                    so_order.quantity = obj.quantity
                    so_order.order_category = so_order.department.category
                    so_order.origin_order_category = obj.order_category
                    so_order.create_date = obj.date
                    so_order.origin_order_id = obj.order_id
                    so_order.date = obj.date

                    si_order.price = 0
                    si_order.quantity_received = obj.quantity
                    si_order.quantity_receivable = obj.quantity
                    si_order.order_category = si_order.department.category
                    si_order.origin_order_category = obj.order_category
                    si_order.create_date = obj.date
                    si_order.origin_order_id = obj.order_id
                    si_order.stockin_date = obj.stockin_date

                    fields_list = ['ori_creator', 'goods_id', 'batch_number', 'expiry_date', 'produce_date', 'memorandum']

                    for k in fields_list:
                        if hasattr(obj, k):
                            setattr(so_order, k, getattr(obj, k))  # 更新对象属性对应键值

                    for k in fields_list:
                        if hasattr(obj, k):
                            setattr(si_order, k, getattr(obj, k))  # 更新对象属性对应键值

                    if len(str(so_order.memorandum)) > 300:
                        so_order.memorandum = so_order.memorandum[:300]
                    if len(str(si_order.memorandum)) > 300:
                        si_order.memorandum = si_order.memorandum[:300]

                    try:
                        so_order.creator = self.request.user.username
                        si_order.creator = self.request.user.username
                        so_order.save()
                        si_order.save()
                    except Exception as e:
                        self.message_user("单号%s实例保存出错：%s" % (obj.order_id, e), "error")
                        n -= 1
                        obj.mistake_tag = 6
                        obj.save()
                        continue
                    obj.order_status = 2
                    obj.mistake_tag = 0
                    obj.save()

            self.message_user("成功提交 %(count)d %(items)s." % {"count": n, "items": model_ngettext(self.opts, n)},
                              'success')

        return None


# #####未递交原始直接调拨单#####
class OriALUnhandleAdmin(object):
    list_display = ['order_status', 'mistake_tag', 'detail_num', 'order_id', 'order_category', 'trans_in', 'date', 'trans_out',
                    'department', 'memorandum', 'ori_creator', 'goods_id', 'goods_name', 'goods_size', 'batch_num',
                    'quantity', 'warehouse_out', 'warehouse_in', 'produce_date', 'expiry_date', 'stockin_date',
                    'customer']

    list_filter = ['mistake_tag', 'order_status', 'trans_in', 'date', 'trans_out', 'department', 'memorandum',
                   'ori_creator', 'goods_id', 'goods_name', 'goods_size', 'batch_num', 'quantity', 'warehouse_out',
                   'warehouse_in', 'produce_date', 'expiry_date', 'stockin_date', 'customer']

    search_fields = ['order_id', ]
    actions = [OriAllocationAction, RejectSelectedAction]
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
                self.message_user('错误提示：%s' % result)
        return super(OriALUnhandleAdmin, self).post(request, *args, **kwargs)

    def handle_upload_file(self, _file):
        INIT_FIELDS_DIC = {
            '明细信息行号': 'detail_num',
            '单据编号': 'order_id',
            '单据类型': 'order_category',
            '调入库存组织': 'trans_in',
            '日期': 'date',
            '调出库存组织': 'trans_out',
            '销售部门': 'department',
            '备注': 'memorandum',
            '创建人': 'ori_creator',
            '物料编码': 'goods_id',
            '物料名称': 'goods_name',
            '规格型号': 'goods_size',
            '调出批号': 'batch_num',
            '调拨数量': 'quantity',
            '调出仓库': 'warehouse_out',
            '调入仓库': 'warehouse_in',
            '生产日期': 'produce_date',
            '有效期至': 'expiry_date',
            '入库日期': 'stockin_date',
            '客户': 'customer',
        }
        ALLOWED_EXTENSIONS = ['xls', 'xlsx']
        report_dic = {"successful": 0, "discard": 0, "false": 0, "repeated": 0, "error": []}

        if '.' in _file.name and _file.name.rsplit('.')[-1] in ALLOWED_EXTENSIONS:
            with pd.ExcelFile(_file) as xls:
                df = pd.read_excel(xls, sheet_name=0)
                FILTER_FIELDS = ['明细信息行号', '单据编号', '单据类型', '调入库存组织', '日期', '调出库存组织', '销售部门',
                                 '备注', '创建人', '物料编码', '物料名称', '规格型号', '调出批号', '调拨数量', '调出仓库',
                                 '调入仓库', '生产日期', '有效期至', '入库日期', '客户']

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
                _ret_verify_field = OriALUnhandle.verify_mandatory(columns_key)
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
                _ret_verify_field = OriALUnhandle.verify_mandatory(columns_key)
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
            detail_num = row["detail_num"]
            if detail_num == '合计':
                break

            order = OriALUnhandle()  # 创建表格每一行为一个对象
            for k, v in row.items():
                if re.match(r'^=', str(v)):
                    row[k] = v.replace('=', '').replace('"', '')

            order_id = str(row["order_id"])
            row['order_id'] = order_id
            detail_num = row['detail_num']

            # 如果订单号查询，已经存在，丢弃订单，计数为重复订单
            if OriAllocation.objects.filter(order_id=order_id, detail_num=detail_num).exists():
                report_dic["repeated"] += 1
                report_dic["error"].append('%s单据重复导入' % order_id)
                continue
            try:
                row['date'] = datetime.datetime.strptime(row['date'], '%Y/%m/%d')
                row['stockin_date'] = datetime.datetime.strptime(row['stockin_date'], '%Y/%m/%d')
            except Exception as e:
                print(e)
                continue
            try:
                row['produce_date'] = datetime.datetime.strptime(row['produce_date'], '%Y/%m/%d')
                row['expiry_date'] = datetime.datetime.strptime(row['expiry_date'], '%Y/%m/%d')
            except Exception as e:
                row['produce_date'] = row['date']
                row['expiry_date'] = row['date'] + datetime.timedelta(days=180)


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

    def queryset(self):
        queryset = super(OriALUnhandleAdmin, self).queryset()
        queryset = queryset.filter(is_delete=0, order_status=1)
        return queryset

    def has_add_permission(self):
        # 禁用添加按钮
        return False


# 原始直接调拨单
class OriAllocationAdmin(object):
    list_display = ['order_status', 'mistake_tag', 'detail_num', 'order_id', 'order_category', 'trans_in', 'date', 'trans_out',
                    'department', 'memorandum', 'ori_creator', 'goods_id', 'goods_name', 'goods_size', 'batch_num',
                    'quantity', 'warehouse_out', 'warehouse_in', 'produce_date', 'expiry_date', 'stockin_date',
                    'customer']

    list_filter = ['mistake_tag', 'order_status', 'trans_in', 'date', 'trans_out', 'department', 'memorandum',
                   'ori_creator', 'goods_id', 'goods_name', 'goods_size', 'batch_num', 'quantity', 'warehouse_out',
                   'warehouse_in', 'produce_date', 'expiry_date', 'stockin_date', 'customer']

    search_fields = ['order_id', ]

    def has_add_permission(self):
        # 禁用添加按钮
        return False


# 递交原始盘盈单
class OriSUAction(BaseActionView):
    action_name = "submit_npsi_ori"
    description = "提交选中的订单"
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
                    order_id = '{0}-{1}'.format(str(obj.order_id), str(obj.detail_num))
                    if CovertSI.objects.filter(order_id=order_id).exists():
                        self.message_user("单号%s递交重复，检查问题" % obj.order_id, "error")
                        n -= 1
                        obj.mistake_tag = 1
                        obj.save()
                        continue
                    order = CovertSI()
                    order.order_id = order_id
                    supplier = obj.owner
                    order.payee = supplier
                    order.purchaser = supplier
                    _q_supplier = CompanyInfo.objects.filter(company_name=supplier)
                    if _q_supplier.exists():
                        order.supplier = _q_supplier[0]
                    else:
                        self.message_user("单号%s供货商非法，查看系统是否有此供货商" % obj.order_id, "error")
                        n -= 1
                        obj.mistake_tag = 2
                        obj.save()
                        continue

                    _q_department = DepartmentInfo.objects.filter(name='物流部')
                    if _q_department.exists():
                        order.department = _q_department[0]
                    else:
                        self.message_user("单号%s部门非法，查看系统是否有此部门" % obj.order_id, "error")
                        n -= 1
                        obj.mistake_tag = 3
                        obj.save()
                        continue
                    goods = obj.goods_id
                    _q_goods = GoodsInfo.objects.filter(goods_id=goods)
                    if _q_goods.exists():
                        order.goods_name = _q_goods[0]
                    else:
                        self.message_user("单号%s货品非法，查看系统是否有货品" % obj.order_id, "error")
                        n -= 1
                        obj.mistake_tag = 4
                        obj.save()
                        continue
                    warehouse = obj.warehouse
                    _q_warehouse = WarehouseGeneral.objects.filter(warehouse_name=warehouse)
                    if _q_warehouse.exists():
                        order.warehouse = _q_warehouse[0]
                    else:
                        self.message_user("单号%s仓库错误，查看系统是否有此仓库" % obj.order_id, "error")
                        n -= 1
                        obj.mistake_tag = 5
                        obj.save()
                        continue

                    order.price = 0
                    order.quantity_received = obj.quantity
                    order.quantity_receivable = obj.quantity
                    order.order_category = order.department.category
                    order.origin_order_category = obj.order_category
                    order.create_date = obj.date
                    order.stockin_date = obj.date
                    order.origin_order_id = obj.order_id

                    fields_list = ['ori_creator', 'memorandum', 'goods_id', 'batch_num', 'produce_date', 'expiry_date']

                    for k in fields_list:
                        if hasattr(obj, k):
                            setattr(order, k, getattr(obj, k))  # 更新对象属性对应键值

                    if len(str(order.memorandum)) > 300:
                        order.memorandum = order.memorandum[:300]
                    try:
                        order.creator = self.request.user.username
                        order.save()
                    except Exception as e:
                        self.message_user("单号%s实例保存出错：%s" % (obj.order_id, e), "error")
                        n -= 1
                        obj.mistake_tag = 6
                        obj.save()
                        continue
                    obj.order_status = 2
                    obj.mistake_tag = 0
                    obj.save()

            self.message_user("成功提交 %(count)d %(items)s." % {"count": n, "items": model_ngettext(self.opts, n)},
                              'success')

        return None


# #####未递交原始盘盈单#####
class OriSUUnhandleAdmin(object):
    list_display = ['order_status', 'mistake_tag', 'detail_num', 'order_id', 'order_category', 'date', 'ori_creator', 'owner',
                    'memorandum', 'goods_id', 'goods_name', 'goods_size', 'stock', 'check', 'quantity', 'warehouse',
                    'batch_num', 'produce_date', 'expiry_date']

    list_filter = ['mistake_tag', 'order_status', 'date', 'ori_creator', 'memorandum', 'goods_id', 'goods_name',
                   'goods_size', 'stock', 'check', 'quantity', 'warehouse', 'batch_num', 'produce_date', 'expiry_date']

    search_fields = ['order_id', ]
    actions = [OriSUAction, RejectSelectedAction]
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
                self.message_user('错误提示：%s' % result)
        return super(OriSUUnhandleAdmin, self).post(request, *args, **kwargs)

    def handle_upload_file(self, _file):
        INIT_FIELDS_DIC = {
            '明细信息行号': 'detail_num',
            '单据编号': 'order_id',
            '单据类型': 'order_category',
            '日期': 'date',
            '创建人': 'ori_creator',
            '货主': 'owner',
            '备注': 'memorandum',
            '物料编码': 'goods_id',
            '物料名称': 'goods_name',
            '规格型号': 'goods_size',
            '账存数量': 'stock',
            '盘点数量': 'check',
            '盘盈数量': 'quantity',
            '仓库': 'warehouse',
            '批号': 'batch_num',
            '生产日期': 'produce_date',
            '到期日': 'expiry_date',
        }
        ALLOWED_EXTENSIONS = ['xls', 'xlsx']
        report_dic = {"successful": 0, "discard": 0, "false": 0, "repeated": 0, "error": []}

        if '.' in _file.name and _file.name.rsplit('.')[-1] in ALLOWED_EXTENSIONS:
            with pd.ExcelFile(_file) as xls:
                df = pd.read_excel(xls, sheet_name=0)
                FILTER_FIELDS = ['明细信息行号', '单据编号', '单据类型', '日期', '创建人', '货主', '备注', '物料编码',
                                 '物料名称', '规格型号', '账存数量', '盘点数量', '盘盈数量', '仓库', '批号', '生产日期', '到期日']

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
                _ret_verify_field = OriSUUnhandle.verify_mandatory(columns_key)
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
                _ret_verify_field = OriSUUnhandle.verify_mandatory(columns_key)
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
            detail_num = row["detail_num"]
            if detail_num == '合计':
                break

            order = OriSUUnhandle()  # 创建表格每一行为一个对象
            for k, v in row.items():
                if re.match(r'^=', str(v)):
                    row[k] = v.replace('=', '').replace('"', '')

            order_id = str(row["order_id"])
            row['order_id'] = order_id
            detail_num = row['detail_num']

            # 如果订单号查询，已经存在，丢弃订单，计数为重复订单
            if OriSurplus.objects.filter(order_id=order_id, detail_num=detail_num).exists():
                report_dic["repeated"] += 1
                report_dic["error"].append('%s单据重复导入' % order_id)
                continue

            row['date'] = datetime.datetime.strptime(row['date'], '%Y/%m/%d')
            try:
                row['produce_date'] = datetime.datetime.strptime(row['produce_date'], '%Y/%m/%d')
                row['expiry_date'] = datetime.datetime.strptime(row['expiry_date'], '%Y/%m/%d')
            except Exception as e:
                row['produce_date'] = row['date']
                row['expiry_date'] = row['date'] + datetime.timedelta(days=180)

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

    def queryset(self):
        queryset = super(OriSUUnhandleAdmin, self).queryset()
        queryset = queryset.filter(is_delete=0, order_status=1)
        return queryset

    def has_add_permission(self):
        # 禁用添加按钮
        return False


# 原始盘盈单
class OriSurplusAdmin(object):

    list_display = ['order_status', 'mistake_tag', 'detail_num', 'order_id', 'order_category', 'date', 'ori_creator', 'owner',
                    'memorandum', 'goods_id', 'goods_name', 'goods_size', 'stock', 'check', 'quantity', 'warehouse',
                    'batch_num', 'produce_date', 'expiry_date']

    list_filter = ['mistake_tag', 'order_status', 'date', 'ori_creator', 'memorandum', 'goods_id', 'goods_name',
                   'goods_size', 'stock', 'check', 'quantity', 'warehouse', 'batch_num', 'produce_date', 'expiry_date']

    search_fields = ['order_id', ]

    def has_add_permission(self):
        # 禁用添加按钮
        return False


# 递交原始盘亏单
class OriLOAction(BaseActionView):
    action_name = "submit_loss_ori"
    description = "提交选中的订单"
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
                    order_id = '{0}-{1}'.format(str(obj.order_id), str(obj.detail_num))
                    if CovertSO.objects.filter(order_id=order_id).exists():
                        self.message_user("单号%s递交重复，检查问题" % obj.order_id, "error")
                        n -= 1
                        obj.mistake_tag = 1
                        obj.save()
                        continue
                    order = CovertSO()
                    order.order_id = order_id

                    _q_department = DepartmentInfo.objects.filter(name='物流部')
                    if _q_department.exists():
                        order.department = _q_department[0]
                    else:
                        self.message_user("单号%s部门非法，查看系统是否有此部门" % obj.order_id, "error")
                        n -= 1
                        obj.mistake_tag = 2
                        obj.save()
                        continue
                    goods = obj.goods_id
                    _q_goods = GoodsInfo.objects.filter(goods_id=goods)
                    if _q_goods.exists():
                        order.goods_name = _q_goods[0]
                    else:
                        self.message_user("单号%s货品非法，查看系统是否有货品" % obj.order_id, "error")
                        n -= 1
                        obj.mistake_tag = 3
                        obj.save()
                        continue
                    warehouse = obj.warehouse
                    _q_warehouse = WarehouseGeneral.objects.filter(warehouse_name=warehouse)
                    if _q_warehouse.exists():
                        order.warehouse = _q_warehouse[0]
                    else:
                        self.message_user("单号%s仓库错误，查看系统是否有此仓库" % obj.order_id, "error")
                        n -= 1
                        obj.mistake_tag = 4
                        obj.save()
                        continue

                    obj.customer = '盘点亏损'
                    order.order_category = order.department.category
                    order.origin_order_category = obj.order_category
                    order.origin_order_id = obj.order_id
                    order.price = 0
                    order.amount = 0

                    fields_list = ['ori_creator', 'memorandum', 'goods_id', 'batch_num', 'produce_date', 'expiry_date',
                                   'date', 'quantity']

                    for k in fields_list:
                        if hasattr(obj, k):
                            setattr(order, k, getattr(obj, k))  # 更新对象属性对应键值

                    if len(str(order.memorandum)) > 300:
                        order.memorandum = order.memorandum[:300]

                    try:
                        order.creator = self.request.user.username
                        order.save()
                    except Exception as e:
                        self.message_user("单号%s实例保存出错：%s" % (obj.order_id, e), "error")
                        n -= 1
                        obj.mistake_tag = 5
                        obj.save()
                        continue
                    obj.order_status = 2
                    obj.mistake_tag = 0
                    obj.save()

            self.message_user("成功提交 %(count)d %(items)s." % {"count": n, "items": model_ngettext(self.opts, n)},
                              'success')

        return None


# #####未递交原始盘亏单#####
class OriLOUnhandleAdmin(object):
    list_display = ['order_status', 'mistake_tag', 'detail_num', 'order_id', 'order_category', 'date', 'ori_creator', 'owner',
                    'memorandum', 'goods_id', 'goods_name', 'goods_size', 'stock', 'check', 'quantity', 'warehouse',
                    'batch_num', 'produce_date', 'expiry_date']

    list_filter = ['mistake_tag', 'order_status', 'date', 'ori_creator', 'memorandum', 'goods_id', 'goods_name',
                   'goods_size', 'stock', 'check', 'quantity', 'warehouse', 'batch_num', 'produce_date', 'expiry_date']

    search_fields = ['order_id', ]
    actions = [OriLOAction, RejectSelectedAction]
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
                self.message_user('错误提示：%s' % result)
        return super(OriLOUnhandleAdmin, self).post(request, *args, **kwargs)

    def handle_upload_file(self, _file):
        INIT_FIELDS_DIC = {
            '明细信息行号': 'detail_num',
            '单据编号': 'order_id',
            '单据类型': 'order_category',
            '日期': 'date',
            '创建人': 'ori_creator',
            '货主': 'owner',
            '备注': 'memorandum',
            '物料编码': 'goods_id',
            '物料名称': 'goods_name',
            '规格型号': 'goods_size',
            '账存数量': 'stock',
            '盘点数量': 'check',
            '盘亏数量': 'quantity',
            '仓库': 'warehouse',
            '批号': 'batch_num',
            '生产日期': 'produce_date',
            '有效期至': 'expiry_date',
        }
        ALLOWED_EXTENSIONS = ['xls', 'xlsx']
        report_dic = {"successful": 0, "discard": 0, "false": 0, "repeated": 0, "error": []}

        if '.' in _file.name and _file.name.rsplit('.')[-1] in ALLOWED_EXTENSIONS:
            with pd.ExcelFile(_file) as xls:
                df = pd.read_excel(xls, sheet_name=0)
                FILTER_FIELDS = ['明细信息行号', '单据编号', '单据类型', '日期', '创建人', '货主', '备注', '物料编码',
                                 '物料名称', '规格型号', '账存数量', '盘点数量', '盘亏数量', '仓库', '批号', '生产日期',
                                 '有效期至']

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
                _ret_verify_field = OriLOUnhandle.verify_mandatory(columns_key)
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
                _ret_verify_field = OriLOUnhandle.verify_mandatory(columns_key)
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
            detail_num = row["detail_num"]
            if detail_num == '合计':
                break

            order = OriLOUnhandle()  # 创建表格每一行为一个对象
            for k, v in row.items():
                if re.match(r'^=', str(v)):
                    row[k] = v.replace('=', '').replace('"', '')

            order_id = str(row["order_id"])
            row['order_id'] = order_id
            detail_num = row['detail_num']
            if str(row['check']) in ['nan', 'NaN']:
                row['check'] = 0
            # 如果订单号查询，已经存在，丢弃订单，计数为重复订单
            if OirLoss.objects.filter(order_id=order_id, detail_num=detail_num).exists():
                report_dic["repeated"] += 1
                report_dic["error"].append('%s单据重复导入' % order_id)
                continue

            row['date'] = datetime.datetime.strptime(row['date'], '%Y/%m/%d')
            try:
                row['produce_date'] = datetime.datetime.strptime(row['produce_date'], '%Y/%m/%d')
                row['expiry_date'] = datetime.datetime.strptime(row['expiry_date'], '%Y/%m/%d')
            except Exception as e:
                row['produce_date'] = row['date']
                row['expiry_date'] = row['date'] + datetime.timedelta(days=180)

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

    def queryset(self):
        queryset = super(OriLOUnhandleAdmin, self).queryset()
        queryset = queryset.filter(is_delete=0, order_status=1)
        return queryset

    def has_add_permission(self):
        # 禁用添加按钮
        return False


# 原始盘亏单
class OirLossAdmin(object):
    list_display = ['order_status', 'mistake_tag', 'detail_num', 'order_id', 'order_category', 'date', 'ori_creator', 'owner',
                    'memorandum', 'goods_id', 'goods_name', 'goods_size', 'stock', 'check', 'quantity', 'warehouse',
                    'batch_num', 'produce_date', 'expiry_date']

    list_filter = ['mistake_tag', 'order_status', 'date', 'ori_creator', 'memorandum', 'goods_id', 'goods_name',
                   'goods_size', 'stock', 'check', 'quantity', 'warehouse', 'batch_num', 'produce_date', 'expiry_date']

    search_fields = ['order_id', ]

    def has_add_permission(self):
        # 禁用添加按钮
        return False


# 原始采购单
xadmin.site.register(OriPurchaseUnhandle, OriPurchaseUnhandleAdmin)
xadmin.site.register(OriPurchaseInfo, OriPurchaseInfoAdmin)
# 原始采购入库单
xadmin.site.register(OriStockInUnhandle, OriStockInUnhandleAdmin)
xadmin.site.register(OriStockInInfo, OriStockInInfoAdmin)
# 原始销售出库单
xadmin.site.register(OriStockOutUnhandle, OriStockOutUnhandleAdmin)
xadmin.site.register(OriStockOut, OriStockOutAdmin)
# 原始其他出库单
xadmin.site.register(OriNSSOUnhandle, OriNSSOUnhandleAdmin)
xadmin.site.register(OriNSStockout, OriNSStockoutAdmin)
# 原始其他入库单
xadmin.site.register(OriNPSIUnhandle, OriNPSIUnhandleAdmin)
xadmin.site.register(OriNPStockIn, OriNPStockInAdmin)
# 原始销售退货单
xadmin.site.register(OriRefundUnhandle, OriRefundUnhandleAdmin)
xadmin.site.register(OriRefund, OriRefundAdmin)
# 原始采购退料单
xadmin.site.register(OriPRUnhandle, OriPRUnhandleAdmin)
xadmin.site.register(OriPurRefund, OriPurRefundAdmin)
# 原始直接调拨单
xadmin.site.register(OriALUnhandle, OriALUnhandleAdmin)
xadmin.site.register(OriAllocation, OriAllocationAdmin)
# 原始盘盈单
xadmin.site.register(OriSUUnhandle, OriSUUnhandleAdmin)
xadmin.site.register(OriSurplus, OriSurplusAdmin)
# 原始盘亏单
xadmin.site.register(OriLOUnhandle, OriLOUnhandleAdmin)
xadmin.site.register(OirLoss, OirLossAdmin)




