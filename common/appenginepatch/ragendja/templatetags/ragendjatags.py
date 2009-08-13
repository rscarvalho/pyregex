# -*- coding: utf-8 -*-
from copy import deepcopy
from django.forms.forms import NON_FIELD_ERRORS
from django.template import Library
from django.utils.datastructures import SortedDict
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _
from ragendja.dbutils import prefetch_references

register = Library()

register.filter('prefetch_references', prefetch_references)

_js_escapes = {
    '>': r'\x3E',
    '<': r'\x3C',
    '&': r'\x26',
    '=': r'\x3D',
    '-': r'\x2D',
    ';': r'\x3B',
}

@register.filter
def encodejs(value):
    from django.utils import simplejson
    from ragendja.json import LazyEncoder
    value = simplejson.dumps(value, cls=LazyEncoder)
    for bad, good in _js_escapes.items():
        value = value.replace(bad, good)
    return mark_safe(value)

@register.filter
def urlquerybase(url):
    """
    Appends '?' or '&' to an url, so you can easily add extra GET parameters.
    """
    if url:
        if '?' in url:
            url += '&'
        else:
            url += '?'
    return url

@register.simple_tag
def htrans(value):
    """
    Creates a "hidden" translation.

    Translates a string, but doesn't add it to django.po. This is useful
    if you use the same string in multiple apps and don't want to translate
    it in each of them (the translations will get overriden by the last app,
    anyway).
    """
    return _(value)

@register.simple_tag
def exclude_form_fields(form=None, fields=None, as_choice='as_table',
        global_errors=True):
    fields=fields.replace(' ', '').split(',')
    if not global_errors:
        form.errors[NON_FIELD_ERRORS] = form.error_class()
    
    fields_backup = deepcopy(form.fields)
    for field in fields:
        if field in form.fields:
            del form.fields[field]

    resulting_text = getattr(form, as_choice)()
    form.fields = fields_backup
    return resulting_text

@register.simple_tag
def include_form_fields(form=None, fields=None, as_choice='as_table',
        global_errors=True):
    fields=fields.replace(' ', '').split(',')
    if not global_errors:
        form.errors[NON_FIELD_ERRORS] = form.error_class()
    
    fields_backup = deepcopy(form.fields)
                    
    form.fields = SortedDict()
    for field in fields:
        if field in fields_backup:
            form.fields[field] = fields_backup[field]
                
    resulting_text = getattr(form, as_choice)()
    
    form.fields = fields_backup
    return resulting_text

@register.simple_tag
def ordered_form(form=None, fields=None, as_choice='as_table'):
    resulting_text = ''
    if len(form.non_field_errors()) != 0:
        fields_backup = deepcopy(form.fields)
        form.fields = {}
        resulting_text = getattr(form, as_choice)()
        form.fields = fields_backup

    resulting_text = resulting_text + include_form_fields(form, fields,
        as_choice, False) + exclude_form_fields(form, fields, as_choice, False)
    return resulting_text
