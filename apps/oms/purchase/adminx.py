# -*- coding: utf-8 -*-
# @Time    : 2019/11/28 20:56
# @Author  : Hann
# @Site    : 
# @File    : adminx.py
# @Software: PyCharm
import pandas as pd
import re, datetime, math

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

from .models import PurchaseInfo, PurchasePending, OriPurchaseInfo, OriPurchasePending
from apps.base.goods.models import GoodsInfo
from apps.base.company.models import ManuInfo


ACTION_CHECKBOX_NAME = '_selected_action'


class OriSMAction(BaseActionView):
    action_name = "submit_pur_ori"
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
                    repeat_queryset = PurchaseInfo.objects.filter(purchase_order_id=obj.purchase_order_id, goods_id=obj.goods_id)
                    if repeat_queryset.exists():
                        repeat_order = repeat_queryset[0]
                        if repeat_order.price != obj.price:
                            repeat_order.quantity = repeat_order.quantity + obj.quantity
                            repeat_order.save()
                            self.message_user("单号%s，存在合并货品%s" % (obj.purchase_order_id, obj.goods_id), "info")
                            obj.mistake_tag = 1
                            obj.order_status = 2
                            obj.save()
                            continue

                        self.message_user("单号%s重复导入，已生成此货品%s" % (obj.purchase_order_id, obj.goods_id), "error")
                        n -= 1
                        obj.mistake_tag = 2
                        obj.save()
                        continue
                    purchase_order = PurchaseInfo()
                    q_supplier = ManuInfo.objects.filter(company_name=obj.supplier)
                    if q_supplier.exists():
                        supplier = q_supplier[0]
                        purchase_order.supplier = supplier
                    else:
                        self.message_user("单号%s工厂错误，查看系统是否有此工厂" % obj.purchase_order_id, "error")
                        n -= 1
                        obj.mistake_tag = 3
                        obj.save()
                        continue
                    q_goods = GoodsInfo.objects.filter(goods_name=obj.goods_name)
                    if q_goods.exists():
                        goods = q_goods[0]
                        purchase_order.goods_name = goods
                    else:
                        self.message_user("单号%s货品错误，查看系统是否有此货品" % obj.purchase_order_id, "error")
                        n -= 1
                        obj.mistake_tag = 4
                        obj.save()
                        continue
                    fields_list = ['purchase_order_id','purchase_time','status','puchaser','is_cancel','goods_unit','quantity','price','delivery_date','goods_id','is_gift','is_close']

                    for k in fields_list:
                        if hasattr(obj, k):
                            setattr(purchase_order, k, getattr(obj, k))  # 更新对象属性对应键值
                    purchase_order.creator = self.request.user.username
                    purchase_order.save()

                    obj.order_status = 2
                    obj.save()
                    self.message_user("%s 审核完毕" % obj.purchase_order_id, "info")

            self.message_user("成功提交 %(count)d %(items)s." % {"count": n, "items": model_ngettext(self.opts, n)},
                              'success')

        return None


class OriPurchasePendingAdmin(object):
    list_display = ['purchase_order_id', 'mistake_tag', 'order_status', 'purchase_time', 'delivery_date' ,'supplier','puchaser','goods_id','goods_name','quantity', 'goods_unit']
    list_filter = ['purchase_time','mistake_tag','supplier','puchaser','quantity','delivery_date','goods_name',]
    search_fields = ['purchase_order_id', 'goods_name', 'goods_id']
    actions = [OriSMAction, ]
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
        return super(OriPurchasePendingAdmin, self).post(request, args, kwargs)

    def handle_upload_file(self, _file):

        INIT_FIELDS_DIC = {
            '单据编号': 'purchase_order_id',
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
                    for j in range(len(df.loc[:, [i]])):
                        if str(df.at[j, i]) not in ['nan', 'NaN', ' ']:
                            keyword = df.at[j, i]
                        else:
                            df.at[j, i] = keyword
                # 获取表头，对表头进行转换成数据库字段名
                columns_key = df.columns.values.tolist()
                for i in range(len(columns_key)):
                    columns_key[i] = columns_key[i].replace(' ', '').replace('=', '')

                for i in range(len(columns_key)):
                    if INIT_FIELDS_DIC.get(columns_key[i], None) is not None:
                        columns_key[i] = INIT_FIELDS_DIC.get(columns_key[i])

                # 验证一下必要的核心字段是否存在
                _ret_verify_field = OriPurchasePending.verify_mandatory(columns_key)
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
                _ret_verify_field = OriPurchasePending.verify_mandatory(columns_key)
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
            purchase_order_id = row["purchase_order_id"]
            if purchase_order_id == '合计':
                break
            # ERP导出文档添加了等于号，毙掉等于号。
            row['purchase_time'] = datetime.datetime.strptime(row['purchase_time'], '%Y/%m/%d')
            row['delivery_date'] = datetime.datetime.strptime(row['delivery_date'], '%Y/%m/%d %H:%M:%S')
            order = OriPurchasePending()  # 创建表格每一行为一个对象
            for k, v in row.items():
                if re.match(r'^=', str(v)):
                    row[k] = v.replace('=', '').replace('"', '')

            purchase_order_id = str(row["purchase_order_id"])
            goods_id = str(row["goods_id"])
            price = float(row["price"])

            # 如果订单号查询，已经存在，丢弃订单，计数为重复订单
            if OriPurchasePending.objects.filter(purchase_order_id=purchase_order_id, goods_id=goods_id, price=price).exists():
                report_dic["repeated"] += 1
                report_dic["error"].append('%s单据重复导入货品为：%s' % (purchase_order_id, goods_id))
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


class OriPurchaseInfoAdmin(object):
    list_display = ['purchase_order_id', 'purchase_time', 'delivery_date' ,'supplier','puchaser','goods_id','goods_name','quantity', 'goods_unit', 'status',]
    list_filter = ['purchase_time','supplier','puchaser','quantity','delivery_date','goods_name',]
    search_fields = ['purchase_order_id', 'goods_name', 'goods_id']


class PurchaseInfoAdmin(object):
    list_display = ['purchase_order_id','purchase_time','status','goods_name','goods_id','goods_unit','quantity','complete_quantity','price','delivery_date','supplier']


class PurchasePendingAdmin(object):
    pass


xadmin.site.register(OriPurchasePending, OriPurchasePendingAdmin)
xadmin.site.register(OriPurchaseInfo, OriPurchaseInfoAdmin)
xadmin.site.register(PurchaseInfo, PurchaseInfoAdmin)
xadmin.site.register(PurchasePending, PurchasePendingAdmin)


