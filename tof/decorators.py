# -*- coding: utf-8 -*-
# @Author: MaxST
# @Date:   2019-11-17 15:03:06
# @Last Modified by:   MaxST
# @Last Modified time: 2019-12-15 16:25:52
from functools import wraps

from django.db.models import Q
from django.utils.translation import get_language

from .settings import DEFAULT_FILTER_LANGUAGE, DEFAULT_LANGUAGE


def tof_prefetch(*wrapper_args):
    def _tof_prefetch(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            entrys = [
                f'{i}___translations' for i in wrapper_args
                if getattr(getattr(args[0].model, i).field.related_model, '_translations', None)
            ] if wrapper_args else ['_translations']
            return func(*args, **kwargs).prefetch_related(*entrys)

        return wrapper

    return _tof_prefetch


def tof_filter(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        new_args, new_kwargs = args, kwargs
        if hasattr(self.model, '_translations'):
            new_args = []
            for arg in args:
                if isinstance(arg, Q):
                    # modify Q objects (warning: recursion ahead)
                    arg = expand_q_filters(arg, self.model)
                new_args.append(arg)

            new_kwargs = {}
            for key, value in list(kwargs.items()):
                # modify kwargs (warning: recursion ahead)
                new_key, new_value, _ = expand_filter(self.model, key, value)
                new_kwargs.update({new_key: new_value})

        return func(self, *new_args, **new_kwargs)

    return wrapper


def expand_q_filters(q, model):
    new_children = []
    for qi in q.children:
        if isinstance(qi, tuple):
            # this child is a leaf node: in Q this is a 2-tuple of:
            # (filter parameter, value)
            key, value, repl = expand_filter(model, *qi)
            query = Q(**{key: value})
            if repl:
                query |= Q(**{qi[0]: qi[1]})
            new_children.append(query)
        else:
            # this child is another Q node: recursify!
            new_children.append(expand_q_filters(qi, model))
    q.children = new_children
    return q


def expand_filter(model, key, value):
    field_name, sep, lookup = key.partition('__')
    field = getattr(model, field_name)
    from .models import TranslatableField
    if isinstance(field, TranslatableField):
        query = Q(**{f'value{sep}{lookup}': value})
        if DEFAULT_FILTER_LANGUAGE == '__all__':
            pass
        elif DEFAULT_FILTER_LANGUAGE == 'current':
            query &= Q(lang=get_language())
        elif isinstance(DEFAULT_FILTER_LANGUAGE, str):
            query &= Q(lang=DEFAULT_FILTER_LANGUAGE)
        elif isinstance(DEFAULT_FILTER_LANGUAGE, (list, tuple)):
            query &= Q(lang__in=DEFAULT_FILTER_LANGUAGE)
        elif isinstance(DEFAULT_FILTER_LANGUAGE, dict):
            query &= Q(lang__in=DEFAULT_FILTER_LANGUAGE.get(get_language(), (DEFAULT_LANGUAGE, )))
        else:
            query &= Q(lang=get_language())
        return 'id__in', field.translations.filter(query).values_list('object_id', flat=True), True
    return key, value, False
