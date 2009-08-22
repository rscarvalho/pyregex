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

REGEX_FLAGS_LABELS = (
    "Ignore Case", 
    "Make \\w, \\W, \\b, \\B, \\s and \\S dependent on the current locale.",
    "Multi-line Regular Expression",
    "Make the '.' special character match any character at all, including a newline",
    "Make \\w, \\W, \\b, \\B, \\d, \\D, \\s and \\S dependent on the Unicode character properties database.",
    "Verbose"
)

class RegexForm(forms.Form):
    regex = forms.CharField(label="Pattern", required=False,
                            widget=forms.TextInput(attrs={'size': 58}))
    regex_line2 = forms.CharField(label="Pattern", required=False,
                                  widget=forms.Textarea(attrs={'cols': 65, 'rows': 4}))
    regex_method = forms.ChoiceField(label="Method", choices=REGEX_METHODS)
    test_text = forms.CharField(required=False,
                                widget=forms.Textarea(attrs={'cols': 65, 'rows': 4}))
    regex_flags = forms.MultipleChoiceField(choices=REGEX_FLAGS, required=False,
                                            widget=PipedMultiCheckboxField(labels=REGEX_FLAGS_LABELS))
    
    def clean_regex_line2(self):
        cdata = self.cleaned_data
        print self.cleaned_data
        if cdata['regex']:
            regex = cdata['regex']
        else:
            regex = cdata['regex_line2']
            
        self.cleaned_data['regex'] = regex
        
        if not regex:
            raise forms.ValidationError("Please specify a valid regular expression.")
            
        try:
            # If regex is None, force a compile failure
            regex = re.compile(regex)
        except sre_constants.error, e:
            raise forms.ValidationError("Invalid Regexp")
        
        return regex

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