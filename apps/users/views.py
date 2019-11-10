# coding: utf-8

from django.shortcuts import render, redirect
from django.views.generic.base import View


class IndexView(View):
    def get(self, request):
        return redirect('/hana/')