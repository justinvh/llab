def make_bitwise_enumeration(name, values):
    choices = [(p, 1 << i) for i, p in enumerate(values)]
    reverse = [(i, p) for p, i in choices]
    params = dict(choices)
    params['choices'] = choices
    params['value_key'] = dict(reverse)
    return type(name, (object,), params)


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

    def __repr__(self):
        values = dict((self.klass.value_key[i], i) for i in self)
        return 'BitwiseSet([{}])'.format(values)

