# -*- coding: utf-8 -*-
# @Time    : 2019/11/28 21:49
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

from xadmin.plugins.actions import BaseActionView
from xadmin.views.base import filter_hook
from xadmin.util import model_ngettext
from xadmin.layout import Fieldset

from .models import OriStockInPending, OriStockInInfo, StockInInfo
from apps.base.company.models import ManuInfo
from apps.base.goods.models import GoodsInfo
from apps.base.warehouse.models import WarehouseGeneral
from apps.oms.purchase.models import PurchaseInfo
from apps.wms.stock.models import StockInfo, DeptStockInfo

ACTION_CHECKBOX_NAME = '_selected_action'


# 递交原始入库单
class OriSIAction(BaseActionView):
    action_name = "submit_sti_ori"
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
                    stockin_order = StockInInfo()
                    pre_warehouse = WarehouseGeneral.objects.filter(warehouse_name=obj.warehouse)
                    if pre_warehouse.exists():
                        warehouse = pre_warehouse[0]
                        stockin_order.warehouse = warehouse
                    else:
                        self.message_user("单号%s仓库错误，查看系统是否有此仓库" % obj.stockin_order_id, "error")
                        n -= 1
                        obj.mistake_tag = 5
                        obj.save()
                        continue
                    q_goods = GoodsInfo.objects.filter(goods_name=obj.goods_name)
                    if q_goods.exists():
                        goods = q_goods[0]
                        stockin_order.goods_name = goods
                    else:
                        self.message_user("单号%s货品错误，查看系统是否有此货品" % obj.stockin_order_id, "error")
                        n -= 1
                        obj.mistake_tag = 4
                        obj.save()
                        continue
                    pre_purchase = PurchaseInfo.objects.filter(purchase_order_id=obj.stockin_order_id, goods_name=goods)
                    if pre_purchase.exists():
                        purchase_order = pre_purchase[0]
                        stockin_order.purchase_order_id = purchase_order
                    else:
                        self.message_user("单号%s采购单号错误，查看系统是否有此采购单" % obj.stockin_order_id, "error")
                        n -= 1
                        obj.mistake_tag = 6
                        obj.save()
                        continue
                    q_supplier = ManuInfo.objects.filter(company_name=obj.supplier)
                    if q_supplier.exists():
                        supplier = q_supplier[0]
                        stockin_order.supplier = supplier
                    else:
                        self.message_user("单号%s工厂错误，查看系统是否有此工厂" % obj.stockin_order_id, "error")
                        n -= 1
                        obj.mistake_tag = 3
                        obj.save()
                        continue
                    repeat_queryset = StockInInfo.objects.filter(stockin_order_id=obj.stockin_order_id,
                                                                 goods_name=goods, warehouse=warehouse,
                                                                 purchase_order_id=purchase_order,
                                                                 expiry_date=obj.expiry_date)
                    if repeat_queryset.exists():
                        repeat_order = repeat_queryset[0]
                        if repeat_order.quantity_receivable < (obj.quantity_received + repeat_order.quantity_received):
                            repeat_order.quantity_received = obj.quantity_received + repeat_order.quantity_received
                            stockin_order.quantity_linking = stockin_order.quantity_received
                            repeat_order.save()
                            self.message_user("单号%s，合并货品%s" % (obj.stockin_order_id, obj.goods_id), "info")
                            obj.mistake_tag = 1
                            obj.order_status = 2
                            obj.save()
                            continue
                        else:
                            self.message_user("单号%s，重复。货品是%s" % (obj.stockin_order_id, obj.goods_id), "error")
                            obj.mistake_tag = 2
                            obj.order_status = 2
                            obj.save()
                            continue

                    _quantity_receivable = OriStockInInfo.objects.filter(stockin_order_id=obj.stockin_order_id, goods_id=obj.goods_id, warehouse=obj.warehouse, expiry_date=obj.expiry_date, order_status__in=[1, 2])
                    _quantity_receivable = _quantity_receivable.aggregate(quantity_receivable=Sum('quantity_received'))
                    quantity_receivable = _quantity_receivable['quantity_receivable']

                    stockin_order.quantity_receivable = quantity_receivable
                    fields_list = ['order_category','to_organization','order_creator','supplier_address','create_date','seller','bs_category','stockin_order_id','last_modifier','payee','stockin_time','last_modify_time','consignee','is_cancel','purchaser','status','demander','goods_id','goods_size','goods_unit','quantity_receivable','quantity_received','batch_number','expiry_date','produce_time','memorandum','origin_order_category','origin_order_id','payable_quantity','assist_quantity','multiple','price','storage']

                    for k in fields_list:
                        if hasattr(obj, k):
                            setattr(stockin_order, k, getattr(obj, k))  # 更新对象属性对应键值
                    stockin_order.creator = self.request.user.username
                    stockin_order.save()

                    obj.order_status = 2
                    obj.save()
                    self.message_user("%s 递交完毕" % obj.stockin_order_id, "info")

            self.message_user("成功提交 %(count)d %(items)s." % {"count": n, "items": model_ngettext(self.opts, n)},
                              'success')

        return None


# 递交入库单
class SIAction(BaseActionView):
    action_name = "submit_sti_or"
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
                    if obj.quantity_received == obj.quantity_receivable:
                        if obj.purchase_order_id.quantity > obj.purchase_order_id.complete_quantity:
                            obj.purchase_order_id.complete_quantity = obj.purchase_order_id.complete_quantity + obj.quantity_received

                            obj.purchase_order_id.save()

                        obj.order_status = 2
                        obj.save()
                        self.message_user("%s 递交完毕" % obj.stockin_order_id, "info")
                    else:
                        obj.mistake_tag = 2
                        obj.save()
                        self.message_user("%s请递交剩余的原始入库单之后再递交" % obj.stockin_order_id, "info")

            self.message_user("成功提交 %(count)d %(items)s." % {"count": n, "items": model_ngettext(self.opts, n)},
                              'success')

        return None


class OriStockInPendingAdmin(object):
    list_display = ['stockin_order_id', 'mistake_tag', 'order_status', 'supplier', 'create_date', 'purchaser', 'goods_id',
                    'goods_name', 'goods_size', 'goods_unit', 'quantity_receivable', 'quantity_received',
                    'warehouse', 'origin_order_id', 'purchase_order_id', ]
    list_filter = ['mistake_tag', 'supplier', 'goods_id', 'goods_name', 'warehouse', 'origin_order_id', 'purchase_order_id', 'create_date', 'update_time', 'create_time','creator']
    search_fields = []
    actions = [OriSIAction]
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
        return super(OriStockInPendingAdmin, self).post(request, *args, **kwargs)

    def handle_upload_file(self, _file):
        INIT_FIELDS_DIC = {
            '单据类型': 'order_category',
            '对应组织': 'to_organization',
            '创建人': 'order_creator',
            '供货方': 'supplier',
            '供货方地址': 'supplier_address',
            '创建日期': 'create_date',
            '结算方': 'seller',
            '业务类型': 'bs_category',
            '单据编号': 'stockin_order_id',
            '最后修改人': 'last_modifier',
            '收款方': 'payee',
            '入库日期': 'stockin_time',
            '最后修改日期': 'last_modify_time',
            '供应商': 'null01',
            '审核人': 'null02',
            '收料组织': 'consignee',
            '货主': 'null03',
            '审核日期': 'null04',
            '收料部门': 'null05',
            '作废人': 'null06',
            '货主类型': 'null07',
            '库存组': 'null08',
            '作废日期': 'null09',
            '仓管员': 'null10',
            '作废状态': 'is_cancel',
            '采购组织': 'purchaser',
            '单据状态': 'status',
            '采购部门': 'null11',
            '需求组织': 'demander',
            '采购组': 'null12',
            '采购员': 'null13',
            '组织间结算跨法人标识': 'null14',
            '物料编码': 'goods_id',
            '物料名称': 'goods_name',
            '规格型号': 'goods_size',
            '辅助属性': 'null15',
            '辅助属性.是否是退货商品.编码': 'null16',
            '辅助属性.是否是退货商品.名称': 'null17',
            '辅助属性.退货商品.编码': 'null18',
            '辅助属性.退货商品.名称': 'null19',
            '库存单位': 'goods_unit',
            '应收数量': 'quantity_receivable',
            '实收数量': 'quantity_received',
            '成本价': 'price',
            '批号': 'batch_number',
            '仓库': 'warehouse',
            '仓位': 'storage',
            '仓位.一号库仓位.编码': 'null22',
            '仓位.一号库仓位.名称': 'null23',
            '仓位.十号库仓位.名称': 'null24',
            '仓位.十号库仓位.编码': 'null25',
            '仓位.六号库仓位.编码': 'null26',
            '仓位.六号库仓位.名称': 'null27',
            '仓位.二号库仓位.编码': 'null28',
            '仓位.二号库仓位.名称': 'null29',
            '仓位.花印新库仓位.编码': 'null30',
            '仓位.花印新库仓位.名称': 'null31',
            '仓位.四号库仓位.名称': 'null32',
            '仓位.四号库仓位.编码': 'null33',
            '有效期至': 'expiry_date',
            '库存状态': 'null34',
            '生产日期': 'produce_time',
            '备注': 'null35',
            '源单类型': 'origin_order_category',
            '源单编号': 'origin_order_id',
            '关联应付数量（计价基本）': 'payable_quantity',
            '收货库存更新标志': 'null36',
            '已开票数量': 'null37',
            '税率(%)': 'null38',
            '在架寿命期': 'null39',
            '入库库存更新标志': 'null40',
            '是否赠品': 'null41',
            '基本单位': 'null42',
            '关联数量(基本单位)': 'null43',
            '订单单号': 'purchase_order_id',
            '保质期单位': 'null44',
            '实收数量(辅单位)': 'assist_quantity',
            '保质期': 'null45',
            '加工费': 'null46',
            '加工费(本位币)': 'null47',
            '税组合': 'null48',
            'BOM版本': 'null49',
            '税额': 'null50',
            '库存基本数量': 'null51',
            '材料成本': 'null52',
            '材料成本(本位币)': 'null53',
            '系统定价': 'null54',
            '税额(本位币)': 'null55',
            '计价单位': 'null56',
            '价格上限': 'null57',
            '价格下限': 'null58',
            '折扣率(%)': 'null59',
            '金额': 'null60',
            '金额（本位币）': 'null61',
            '价格系数': 'null62',
            '折扣额': 'null63',
            '退料关联数量': 'null64',
            '计划跟踪号': 'null65',
            '供应商批号': 'null66',
            '计价数量': 'null67',
            '数量（库存辅单位）': 'null68',
            '产品类型': 'null69',
            '父项产品': 'null70',
            '行标识': 'null71',
            '净价': 'null72',
            '父行标识': 'null73',
            '总成本': 'null74',
            '总成本(本位币)': 'null75',
            '价税合计': 'null76',
            '价税合计(本位币)': 'null77',
            '需求跟踪号': 'null78',
            '确认人': 'null79',
            '确认日期': 'null80',
            '序列号单位': 'null81',
            '序列号单位数量': 'null82',
            '确认状态': 'null83',
            '仓储入库单编码': 'null84',
            '同步说明': 'null85',
            '审核同步状态': 'null86',
            '样本破坏数量(计价单位)': 'null87',
            '收料更新库存': 'null88',
            '已开票关联数量': 'null89',
            '入库类型': 'null90',
            '计价基本数量': 'null91',
            '定价单位': 'null92',
            '采购单位': 'null93',
            '采购数量': 'null94',
            '采购基本数量': 'null95',
            '采购基本分子': 'null96',
            '库存基本分母': 'null97',
            '携带的主业务单位': 'null98',
            '退料关联数量(采购基本)': 'null99',
            '关联应付数量（库存基本)': 'null100',
            '成本价(本位币)': 'null101',
            '分录价目表': 'null102',
            '未关联应付数量（计价单位）': 'null103',
            '关联应付金额': 'null104',
            '应付关闭状态': 'null105',
            '应付关闭日期': 'null106',
            '拆单新单标识': 'null107',
            '供货方联系人': 'null108',
            '收货人': 'null109',
            '单价折扣': 'null110',
            '主/辅换算率': 'multiple',
            '整箱数': 'null111',
            '散货数量': 'null112',
            '分录录入方式': 'null113',
            '跨组织采购数量': 'null114',
            '跨组织销售数量': 'null115',
        }
        ALLOWED_EXTENSIONS = ['xls', 'xlsx']
        report_dic = {"successful": 0, "discard": 0, "false": 0, "repeated": 0, "error": []}

        if '.' in _file.name and _file.name.rsplit('.')[-1] in ALLOWED_EXTENSIONS:
            with pd.ExcelFile(_file) as xls:
                df = pd.read_excel(xls, sheet_name=0)
                VERIFY_FIELD = ['单据类型', '对应组织', '创建人', '供货方', '供货方地址', '创建日期', '结算方', '业务类型', '单据编号', '最后修改人', '收款方',
                                '入库日期', '最后修改日期', '收料组织', '作废状态', '采购组织', '单据状态', '需求组织', '仓位']
                for i in VERIFY_FIELD:
                    if i == '仓位':
                        keyword = "100000"
                        for j in range(len(df.loc[:, [i]])):
                            if str(df.at[j, i]) in ['nan', 'NaN']:
                                df.at[j, i] = keyword
                    else:
                        keyword = None
                        for j in range(len(df.loc[:, [i]])):
                            if str(df.at[j, i]) not in ['nan', 'NaN']:
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
                _ret_verify_field = OriStockInPending.verify_mandatory(columns_key)
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
                _ret_verify_field = OriStockInPending.verify_mandatory(columns_key)
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
            order_category = row["order_category"]
            if order_category == '合计':
                break
            # ERP导出文档添加了等于号，毙掉等于号。
            order = OriStockInPending()  # 创建表格每一行为一个对象
            for k, v in row.items():
                if re.match(r'^=', str(v)):
                    row[k] = v.replace('=', '').replace('"', '')

            stockin_order_id = str(row["stockin_order_id"])
            status = str(row["status"])
            goods_id = str(row["goods_id"])
            warehouse = str(row['warehouse'])
            price = row['price']
            storage = row['storage']
            batch_number = row['batch_number']

            # 如果订单号查询，已经存在，丢弃订单，计数为重复订单
            if OriStockInInfo.objects.filter(stockin_order_id=stockin_order_id, goods_id=goods_id, warehouse=warehouse, price=price, storage=storage, batch_number=batch_number).exists():
                report_dic["repeated"] += 1
                report_dic["error"].append('%s单据重复导入' % stockin_order_id)
                continue

            row['create_date'] = datetime.datetime.strptime(row['create_date'], '%Y/%m/%d')
            row['stockin_time'] = datetime.datetime.strptime(row['stockin_time'], '%Y/%m/%d')
            row['last_modify_time'] = datetime.datetime.strptime(row['last_modify_time'], '%Y/%m/%d')
            row['produce_time'] = datetime.datetime.strptime(row['produce_time'], '%Y/%m/%d')
            row['expiry_date'] = datetime.datetime.strptime(row['expiry_date'], '%Y/%m/%d')


            # 状态不是'已完成', '待打印', '已打印'，就丢弃这个订单，计数为丢弃订单
            if status not in ['已审核']:
                report_dic["discard"] += 1
                report_dic["error"].append('%s单据状态错误' % stockin_order_id)
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


class OriStockInInfoAdmin(object):
    pass


class StockInInfoAdmin(object):
    list_display = ['order_category', 'supplier', 'create_date', 'stockin_order_id', 'purchaser', 'goods_id',
                    'goods_name', 'goods_size', 'goods_unit', 'quantity_receivable', 'quantity_received',
                    'warehouse', 'origin_order_id', 'purchase_order_id', ]

    actions = [SIAction]


xadmin.site.register(OriStockInPending, OriStockInPendingAdmin)
xadmin.site.register(OriStockInInfo, OriStockInInfoAdmin)
xadmin.site.register(StockInInfo, StockInInfoAdmin)

