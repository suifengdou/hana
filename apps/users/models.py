# -*- coding:utf-8 -*-

from datetime import datetime

from django.db import models
from django.contrib.auth.models import AbstractUser


from db.base_model import BaseModel
from apps.base.company.models import CompanyInfo
from apps.base.department.models import DepartmentInfo


# Create your models here.
class UserProfile(AbstractUser, BaseModel):
    STATUS = (
        (0, '非管理'),
        (1, '管理'),
    )
    nick = models.CharField(max_length=50, verbose_name=u'昵称', default=u'')

    company = models.ForeignKey(CompanyInfo, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='所属公司')
    department = models.ForeignKey(DepartmentInfo, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='所属部门')

    class Meta:
        verbose_name = u'USR-用户信息'
        verbose_name_plural = verbose_name
        db_table = 'users_userprofile'

    def __str__(self):
        return self.username