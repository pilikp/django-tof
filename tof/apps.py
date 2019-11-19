# -*- coding: utf-8 -*-
# @Author: MaxST
# @Date:   2019-10-29 10:05:01
# @Last Modified by:   MaxST
# @Last Modified time: 2019-11-19 14:34:08
import sys

from django.apps import AppConfig
from django.db import connection


class TofConfig(AppConfig):
    """Класс настроек приложения.

    Тут будем при старте сервера кэшировать список переводимых полей

    Attributes:
        name: Имя приложения
    """
    name = 'tof'

    def ready(self):
        # Exception if did not make migration
        if connection.introspection.table_names():
            for arg in ('migrate', 'makemigrations'):
                if arg in sys.argv:
                    return
            for field in self.models_module.TranslatableField.objects.all():
                cls = field.content_type.model_class()
                self.models_module.prepare_cls_for_translate(cls, field)
