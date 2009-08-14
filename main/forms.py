#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pyregex - A Google AppEngine application to test python regular expressions
# Copyright (C) 2009  Rodolfo Carvalho
# 
# Author: Rodolfo Carvalho <rodolfo@rcarvalho.eti.br>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#

import re
import sre_constants
from django import forms
from main.widgets import PipedMultiCheckboxField

REGEX_METHODS = (
    ("match", "match",),
    ("findall", "findall",),
    ("search", "search",)
)

REGEX_FLAGS = (
    (re.I, "re.I"),
    (re.L, "re.L"),
    (re.M, "re.M"),
    (re.S, "re.S"),
    (re.U, "re.U"),
    (re.X, "re.X"),
)

class RegexForm(forms.Form):
    regex = forms.CharField(label="Pattern", required=True,
                            widget=forms.TextInput(attrs={'size': 70}))
    regex_method = forms.ChoiceField(label="Method", choices=REGEX_METHODS)
    test_text = forms.CharField(required=False,
                                widget=forms.Textarea(attrs={'cols': 65, 'rows': 15}))
    regex_flags = forms.MultipleChoiceField(choices=REGEX_FLAGS, required=False,
                                            widget=PipedMultiCheckboxField)
    
    def clean_regex(self):
        cdata = self.cleaned_data
        try:
            # If regex is None, force a compile failure
            regex = re.compile(cdata['regex'])
        except sre_constants.error, e:
            raise forms.ValidationError("Invalid Regexp")
        
        return cdata['regex']

    def clean_regex_flags(self):
        rflags = self.cleaned_data['regex_flags']
        flags = 0
        if rflags:
            for flag in rflags:
                flags |= int(flag)
            return flags
        return flags
        
    @property
    def regex_pattern(self):
        return re.compile(self.cleaned_data['regex'], self.cleaned_data['regex_flags'])