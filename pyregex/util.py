import types

class ValueMeta(type):
    def __new__(cls, name, bases, dct):
        obj = type.__new__(cls, name, bases, dct)

        old_setattr = obj.__setattr__

        def _setattr(self, *args):
            if hasattr(self, '__immutable__') and self.__immutable__:
                raise TypeError("can't modify immutable instance")
            old_setattr(self, *args)

        obj.__setattr__ = _setattr
        obj.__delattr__ = _setattr

        return obj

    def __call__(cls, *args, **kwargs):
        obj = type.__call__(cls, *args, **kwargs)
        obj.__immutable__ = True
        return obj


class Value(object, metaclass=ValueMeta):
    def __init__(self, **kwargs):
        for key in kwargs:
            setattr(self, key, kwargs[key])


def dict_from_object(obj):
    if obj and hasattr(obj, 'groupdict') and callable(getattr(obj, 'groupdict')):
        return dict(
            group=obj.group(),
            groups=obj.groups(),
            group_dict=obj.groupdict(),
            end=obj.end(), start=obj.start(), pos=obj.pos,
            span=obj.span(),
            regs=obj.regs,
            last_group=obj.lastgroup,
            last_index=obj.lastindex
        )
    elif not obj:
        return None
    return obj
