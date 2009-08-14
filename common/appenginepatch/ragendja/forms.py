from copy import deepcopy
import re

from django import forms
from django.utils.datastructures import SortedDict, MultiValueDict
from django.utils.html import conditional_escape
from django.utils.encoding import StrAndUnicode, smart_unicode, force_unicode
from django.utils.safestring import mark_safe
from django.forms.widgets import flatatt
from google.appengine.ext import db

class FakeModelIterator(object):
    def __init__(self, fake_model):
        self.fake_model = fake_model
    
    def __iter__(self):
        for item in self.fake_model.all():
            yield (item.get_value_for_datastore(), unicode(item))

class FakeModelChoiceField(forms.ChoiceField):
    def __init__(self, fake_model, *args, **kwargs):
        self.fake_model = fake_model
        kwargs['choices'] = ()
        super(FakeModelChoiceField, self).__init__(*args, **kwargs)

    def _get_choices(self):
        return self._choices
    def _set_choices(self, choices):
        self._choices = self.widget.choices = FakeModelIterator(self.fake_model)
    choices = property(_get_choices, _set_choices)

    def clean(self, value):
        value = super(FakeModelChoiceField, self).clean(value)
        return self.fake_model.make_value_from_datastore(value)

class FakeModelMultipleChoiceField(forms.MultipleChoiceField):
    def __init__(self, fake_model, *args, **kwargs):
        self.fake_model = fake_model
        kwargs['choices'] = ()
        super(FakeModelMultipleChoiceField, self).__init__(*args, **kwargs)

    def _get_choices(self):
        return self._choices
    def _set_choices(self, choices):
        self._choices = self.widget.choices = FakeModelIterator(self.fake_model)
    choices = property(_get_choices, _set_choices)

    def clean(self, value):
        value = super(FakeModelMultipleChoiceField, self).clean(value)
        return [self.fake_model.make_value_from_datastore(item)
                for item in value]

class FormWithSets(object):
    def __init__(self, form, formsets=()):
        self.form = form
        setattr(self, '__module__', form.__module__)
        setattr(self, '__name__', form.__name__ + 'WithSets')
        setattr(self, '__doc__', form.__doc__)
        self._meta = form._meta
        fields = [(name, field) for name, field in form.base_fields.iteritems() if isinstance(field, FormSetField)]
        formset_dict = dict(formsets)
        newformsets = []
        for name, field in fields:
            if formset_dict.has_key(name):
                continue
            newformsets.append((name, {'formset':field.make_formset(form._meta.model)}))
        self.formsets = formsets + tuple(newformsets)

    def __call__(self, *args,  **kwargs):
        prefix = kwargs['prefix'] + '-' if 'prefix' in kwargs else ''
        form = self.form(*args,  **kwargs)
        if 'initial' in kwargs:
            del kwargs['initial']
        formsets = []
        for name, formset in self.formsets:
            kwargs['prefix'] = prefix + name
            instance = formset['formset'](*args, **kwargs)
            if form.base_fields.has_key(name):
                field = form.base_fields[name]
            else:
                field = FormSetField(formset['formset'].model, **formset)
            formsets.append(BoundFormSet(field, instance, name, formset))
        return type(self.__name__ + 'Instance', (FormWithSetsInstance, ), {})(self, form, formsets)

def pretty_name(name):
    "Converts 'first_name' to 'First name'"
    name = name[0].upper() + name[1:]
    return name.replace('_', ' ')

table_sections_re = re.compile(r'^(.*?)(<tr>.*</tr>)(.*?)$', re.DOTALL)
table_row_re = re.compile(r'(<tr>(<th><label.*?</label></th>)(<td>.*?</td>)</tr>)', re.DOTALL)
ul_sections_re = re.compile(r'^(.*?)(<li>.*</li>)(.*?)$', re.DOTALL)
ul_row_re = re.compile(r'(<li>(<label.*?</label>)(.*?)</li>)', re.DOTALL)
p_sections_re = re.compile(r'^(.*?)(<p>.*</p>)(.*?)$', re.DOTALL)
p_row_re = re.compile(r'(<p>(<label.*?</label>)(.*?)</p>)', re.DOTALL)
label_re = re.compile(r'^(.*)<label for="id_(.*?)">(.*)</label>(.*)$')
hidden_re = re.compile(r'(<input type="hidden".* />)', re.DOTALL)

class BoundFormSet(StrAndUnicode):
    def __init__(self, field, formset, name, args):
        self.field = field
        self.formset = formset
        self.name = name
        self.args = args
        if self.field.label is None:
            self.label = pretty_name(name)
        else:
            self.label = self.field.label
        self.auto_id = self.formset.auto_id % self.formset.prefix
        if args.has_key('attrs'):
            self.attrs = args['attrs'].copy()
        else:
            self.attrs = {}

    def __unicode__(self):
        """Renders this field as an HTML widget."""
        return self.as_widget()

    def as_widget(self, attrs=None):
        """
        Renders the field by rendering the passed widget, adding any HTML
        attributes passed as attrs.  If no widget is specified, then the
        field's default widget will be used.
        """
        attrs = attrs or {}
        auto_id = self.auto_id
        if auto_id and 'id' not in attrs and not self.args.has_key('id'):
            attrs['id'] = auto_id
        try:
            data = self.formset.as_table()
            name = self.name
            return self.render(name, data, attrs=attrs)
        except Exception, e:
            import traceback
            return traceback.format_exc()

    def render(self, name, value, attrs=None):
        table_sections = table_sections_re.search(value).groups()
        output = []
        heads = []
        current_row = []
        first_row = True
        first_head_id = None
        prefix = 'id_%s-%%s-' % self.formset.prefix
        for row, head, item in table_row_re.findall(table_sections[1]):
            if first_row:
                head_groups = label_re.search(head).groups()
                if first_head_id == head_groups[1]:
                    first_row = False
                    output.append(current_row)
                    current_row = []
                else:
                    heads.append('%s%s%s' % (head_groups[0], head_groups[2], head_groups[3]))
                    if first_head_id is None:
                        first_head_id = head_groups[1].replace('-0-','-1-')
            current_row.append(item)
            if not first_row and len(current_row) >= len(heads):
                output.append(current_row)
                current_row = []
        if len(current_row) != 0:
            raise Exception('Unbalanced render')
        return mark_safe(u'%s<table%s><tr>%s</tr><tr>%s</tr></table>%s'%(
            table_sections[0],
            flatatt(attrs),
            u''.join(heads),
            u'</tr><tr>'.join((u''.join(x) for x in output)),
            table_sections[2]))

class CachedQuerySet(object):
    def __init__(self, get_queryset):
        self.queryset_results = (x for x in get_queryset())

    def __call__(self):
        return self.queryset_results

class FormWithSetsInstance(object):
    def __init__(self, master, form, formsets):
        self.master = master
        self.form = form
        self.formsets = formsets
        self.instance = form.instance

    def __unicode__(self):
        return self.as_table()
    
    def is_valid(self):
        result = self.form.is_valid()
        for bf in self.formsets:
            result = bf.formset.is_valid() and result
        return result
    
    def save(self, *args,  **kwargs):
        def save_forms(forms, obj=None):
            for form in forms:
                if not instance and form != self.form:
                    for row in form.forms:
                        row.cleaned_data[form.rel_name] = obj
                form_obj = form.save(*args,  **kwargs)
                if form == self.form:
                    obj = form_obj
            return obj

        instance = self.form.instance
        grouped = []
        ungrouped = []
        # cache the result of get_queryset so that it doesn't run inside the transaction
        for bf in self.formsets:
            if bf.formset.rel_name == 'parent':
                grouped.append(bf.formset)
            else:
                ungrouped.append(bf.formset)
            bf.formset_get_queryset = bf.formset.get_queryset
            bf.formset.get_queryset = CachedQuerySet(bf.formset_get_queryset)
        if grouped:
            grouped.insert(0, self.form)
        else:
            ungrouped.insert(0, self.form)
        obj = None
        if grouped:
            obj = db.run_in_transaction(save_forms, grouped)
        obj = save_forms(ungrouped, obj)
        for bf in self.formsets:
            bf.formset.get_queryset = bf.formset_get_queryset
            del bf.formset_get_queryset
        return obj

    def _html_output(self, form_as, normal_row, help_text_html, sections_re, row_re):
        formsets = SortedDict()
        for bf in self.formsets:
            if bf.label:
                label = conditional_escape(force_unicode(bf.label))
                # Only add the suffix if the label does not end in
                # punctuation.
                if self.form.label_suffix:
                    if label[-1] not in ':?.!':
                        label += self.form.label_suffix
                label = label or ''
            else:
                label = ''
            if bf.field.help_text:
                help_text = help_text_html % force_unicode(bf.field.help_text)
            else:
                help_text = u''
            formsets[bf.name] = {'label': force_unicode(label), 'field': unicode(bf), 'help_text': help_text}

        try:
            output = []
            data = form_as()
            section_search = sections_re.search(data)
            if formsets:
                hidden = u''.join(hidden_re.findall(data))
                last_formset_name, last_formset = formsets.items()[-1]
                last_formset['field'] = last_formset['field'] + hidden
                formsets[last_formset_name] = normal_row % last_formset
                for name, formset in formsets.items()[:-1]:
                    formsets[name] = normal_row % formset

            if not section_search:
                output.append(data)
            else:
                section_groups = section_search.groups()
                for row, head, item in row_re.findall(section_groups[1]):
                    head_search = label_re.search(head)
                    if head_search:
                        id = head_search.groups()[1]
                        if formsets.has_key(id):
                            row = formsets[id]
                            del formsets[id]
                    output.append(row)

            for name, row in formsets.items():
                if name in self.form.fields.keyOrder:
                    output.append(row)

            return mark_safe(u'\n'.join(output))
        except Exception,e:
            import traceback
            return traceback.format_exc()

    def as_table(self):
        "Returns this form rendered as HTML <tr>s -- excluding the <table></table>."
        return self._html_output(self.form.as_table,  u'<tr><th>%(label)s</th><td>%(help_text)s%(field)s</td></tr>', u'<br />%s', table_sections_re, table_row_re)

    def as_ul(self):
        "Returns this form rendered as HTML <li>s -- excluding the <ul></ul>."
        return self._html_output(self.form.as_ul,  u'<li>%(label)s %(help_text)s%(field)s</li>', u' %s', ul_sections_re, ul_row_re)

    def as_p(self):
        "Returns this form rendered as HTML <p>s."
        return self._html_output(self.form.as_p,  u'<p>%(label)s %(help_text)s</p>%(field)s', u' %s', p_sections_re, p_row_re)

    def full_clean(self):
        self.form.full_clean()
        for bf in self.formsets:
            bf.formset.full_clean()

    def has_changed(self):
        result = self.form.has_changed()
        for bf in self.formsets:
            result = bf.formset.has_changed() or result
        return result

    def is_multipart(self):
        result = self.form.is_multipart()
        for bf in self.formsets:
            result = bf.formset.is_multipart() or result
        return result

    @property
    def media(self):
        return mark_safe(unicode(self.form.media) + u'\n'.join([unicode(f.formset.media) for f in self.formsets]))

from django.forms.fields import Field
from django.forms.widgets import Widget
from django.forms.models import inlineformset_factory

class FormSetWidget(Widget):

    def __init__(self, field, attrs=None):
        super(FormSetWidget, self).__init__(attrs)
        self.field = field

    def render(self, name, value, attrs=None):
        if value is None: value = 'FormWithSets decorator required to render %s FormSet' % self.field.model.__name__
        value = force_unicode(value)
        final_attrs = self.build_attrs(attrs, name=name)
        return mark_safe(conditional_escape(value))

class FormSetField(Field):

    def __init__(self, model, widget=FormSetWidget, label=None, initial=None,
                 help_text=None, error_messages=None, show_hidden_initial=False, 
                 formset_factory=inlineformset_factory, *args, **kwargs):
        widget = widget(self)
        super(FormSetField, self).__init__(required=False, widget=widget, label=label, initial=initial, help_text=help_text, error_messages=error_messages, show_hidden_initial=show_hidden_initial)
        self.model = model
        self.formset_factory = formset_factory
        self.args = args
        self.kwargs = kwargs

    def make_formset(self, parent_model):
        return self.formset_factory(parent_model, self.model, *self.args, **self.kwargs)
