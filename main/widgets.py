from itertools import chain

from django import forms
from django.utils.encoding import force_unicode
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe

class PipedMultiCheckboxField(forms.CheckboxSelectMultiple):
    def __init__(self, *args, **kwargs):
        if kwargs.has_key("labels"):
            self.labels = kwargs.pop("labels")
        else:
            self.labels = []
            
        super(PipedMultiCheckboxField, self).__init__(*args, **kwargs)
    
    def render(self, name, value, attrs=None, choices=()):
        if value is None: value = []
        has_id = attrs and 'id' in attrs
        final_attrs = self.build_attrs(attrs, name=name)
        output = [u'']
        str_values = set([force_unicode(v) for v in value])
        for i, (option_value, option_label) in enumerate(chain(self.choices, choices)):
            if has_id:
                final_attrs = dict(final_attrs, id="%s_%s" % (attrs['id'], i))
                label_for = u' for="%s"' % final_attrs['id']
                if i < len(self.labels):
                    final_attrs['title'] = self.labels[i]
                    label_for += u' title="%s"' % self.labels[i]
            else:
                label_for = u''
            
            cb = forms.CheckboxInput(final_attrs, check_test=lambda value: value in str_values)
            option_value = force_unicode(option_value)
            rendered_cb = cb.render(name, option_value)
            option_label = conditional_escape(force_unicode(option_label))
            output.append(u"<label%s>%s %s</label>" % (label_for, rendered_cb, option_label))
        return mark_safe(u" | ".join(output))
