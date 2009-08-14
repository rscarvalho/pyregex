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

from django import forms
import re
import sre_constants

class RegexForm(forms.Form):
    regex = forms.CharField(required=True)
    test_text = forms.CharField(widget=forms.Textarea, required=False)
    
    def clean_regex(self):
        try:
            # If regex is None, force compile to faile
            regex = re.compile(self.cleaned_data.get('regex', '(Invalid Regex'))
        except sre_constants.error, e:
            raise forms.ValidationError("Invalid Regexp")
        
        return regex
