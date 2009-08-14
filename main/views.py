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

from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import Http404, HttpResponse
from main.forms import RegexForm
import re

def index(request):
    if request.method == "POST":
        form = RegexForm(request.POST)
    else:
        form = RegexForm()
    return render_to_response("main/index.html", {'form': form})


def check_regex(request):
    if request.method == "GET":
        raise Http404

    form = RegexForm(request.POST)
    
    if form.is_valid():
        method = getattr(form.cleaned_data['regex'], form.cleaned_data['regex_method'])
        match = method(form.cleaned_data['test_text'])
        
        if hasattr(match, 'dictgroup'):
            result_type = "match"
        elif match is not None:
            result_type = "array"
        else:
            result_type = None
        ctx = {'match': match, 'result_type': result_type}
        return render_to_response("main/result.html", ctx)
    else:
        errors = form.errors
        return HttpResponse("Error: %s" % str(errors))
    