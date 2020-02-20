# -*- coding: utf-8 -*-
# @Author: MaxST
# @Date:   2019-11-17 15:02:55
# @Last Modified by:   MaxST
# @Last Modified time: 2019-11-19 16:40:49
from django.db import models
from django.contrib.contenttypes.models import ContentType

from django.utils.translation import get_language

from .decorators import tof_filter, tof_prefetch


class DecoratedMixIn:
    @tof_filter  # noqa
    def filter(self, *args, **kwargs):  # noqa
        return super().filter(*args, **kwargs)

    @tof_filter  # noqa
    def exclude(self, *args, **kwargs):
        return super().exclude(*args, **kwargs)

    @tof_filter  # noqa
    def get(self, *args, **kwargs):
        return super().get(*args, **kwargs)

    def order_by(self, *args, **kwargs):
        from .models import Translation, TranslatableField
        content_type_id = ContentType.objects.get_for_model(self.model).id
        new_args = []
        subqueries = {}
        for arg in args:
            field_name, rev = arg, ''
            if arg.startswith('-'):
                field_name, rev = arg[1:], arg[0]
            if isinstance(getattr(self.model, field_name), TranslatableField):
                subquery = Translation.objects.filter(object_id=models.OuterRef('pk'), lang=get_language(),
                                                      field=f'{field_name}|{content_type_id}').values('value')
                new_args.append(f'{rev}_{field_name}')
                subqueries[f'_{field_name}'] = subquery
            else:
                new_args.append(arg)
        if args:
            self = self.model.objects.annotate(**subqueries)
        return super().order_by(*new_args, **kwargs)


class TranslationsQuerySet(DecoratedMixIn, models.QuerySet):
    pass


class TranslationManager(DecoratedMixIn, models.Manager):
    default_name = 'trans_objects'
    _queryset_class = TranslationsQuerySet

    def __init__(self, name=None):
        self.default_name = name or self.default_name
        super().__init__()

    @tof_prefetch()
    def get_queryset(self, *args, **kwargs):
        return super().get_queryset(*args, **kwargs)
