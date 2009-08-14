# -*- coding: utf-8 -*-
from django.utils._threading_local import local

def make_tls_property(default=None):
    """Creates a class-wide instance property with a thread-specific value."""
    class TLSProperty(object):
        def __init__(self):
            self.local = local()

        def __get__(self, instance, cls):
            if not instance:
                return self
            return self.value

        def __set__(self, instance, value):
            self.value = value

        def _get_value(self):
            return getattr(self.local, 'value', default)
        def _set_value(self, value):
            self.local.value = value
        value = property(_get_value, _set_value)

    return TLSProperty()

def getattr_by_path(obj, attr, *default):
    """Like getattr(), but can go down a hierarchy like 'attr.subattr'"""
    value = obj
    for part in attr.split('.'):
        if not hasattr(value, part) and len(default):
            return default[0]
        value = getattr(value, part)
        if callable(value):
            value = value()
    return value

def subdict(data, *attrs):
    """Returns a subset of the keys of a dictionary."""
    result = {}
    result.update([(key, data[key]) for key in attrs])
    return result

def equal_lists(left, right):
    """
    Compares two lists and returs True if they contain the same elements, but
    doesn't require that they have the same order.
    """
    right = list(right)
    if len(left) != len(right):
        return False
    for item in left:
        if item in right:
            del right[right.index(item)]
        else:
            return False
    return True

def object_list_to_table(headings, dict_list):
    """
    Converts objects to table-style list of rows with heading:

    Example:
    x.a = 1
    x.b = 2
    x.c = 3
    y.a = 11
    y.b = 12
    y.c = 13
    object_list_to_table(('a', 'b', 'c'), [x, y])
    results in the following (dict keys reordered for better readability):
    [
        ('a', 'b', 'c'),
        (1, 2, 3),
        (11, 12, 13),
    ]
    """
    return [headings] + [tuple([getattr_by_path(row, heading, None)
                                for heading in headings])
                         for row in dict_list]

def dict_list_to_table(headings, dict_list):
    """
    Converts dict to table-style list of rows with heading:

    Example:
    dict_list_to_table(('a', 'b', 'c'),
        [{'a': 1, 'b': 2, 'c': 3}, {'a': 11, 'b': 12, 'c': 13}])
    results in the following (dict keys reordered for better readability):
    [
        ('a', 'b', 'c'),
        (1, 2, 3),
        (11, 12, 13),
    ]
    """
    return [headings] + [tuple([row[heading] for heading in headings])
                         for row in dict_list]
