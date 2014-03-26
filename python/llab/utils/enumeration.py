import json

from collections import OrderedDict

from django.utils.safestring import mark_safe


class PermissionBase(object):
    @classmethod
    def permission_as_int(cls, exclude=[]):
        permission_bitwise = 0
        for name, permission in cls.choices:
            if name in exclude:
                continue
            permission_bitwise |= permission
        return permission_bitwise


def make_bitwise_enumeration(name, values):
    choices = [(p, 1 << i) for i, (p, _) in enumerate(values)]
    long_choices = [(1 << i, l) for i, (_, l) in enumerate(values)]
    reverse = [(i, p) for p, i in choices]
    params = dict(choices)
    params['choices'] = choices
    params['long_choices'] = dict(long_choices)
    params['value_key'] = dict(reverse)
    return type(name, (PermissionBase,), params)


class BitwiseSet(set):
    def __init__(self, klass, instance, field, *args, **kwargs):
        self.field = field
        self.instance = instance
        self.klass = klass
        super(BitwiseSet, self).__init__(*args, **kwargs)

    def add(self, value, *args, **kwargs):
        super(BitwiseSet, self).add(value, *args, **kwargs)
        field = getattr(self.instance, self.field)
        field |= value
        setattr(self.instance, self.field, field)

    def remove(self, value, *args, **kwargs):
        super(BitwiseSet, self).remove(value, *args, **kwargs)
        field = getattr(self.instance, self.field)
        field &= ~value
        setattr(self.instance, self.field, field)

    def as_json(self):
        values = sorted((self.klass.long_choices[i], i) for i in self)
        values = OrderedDict(values)
        return mark_safe(json.dumps(values))

    def __repr__(self):
        values = dict((self.klass.value_key[i], i) for i in self)
        return 'BitwiseSet([{}])'.format(values)
