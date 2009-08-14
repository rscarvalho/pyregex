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
        match = re.match(form.cleaned_data['regex'], form.cleaned_data['test_text'])
        return render_to_response("main/result.html", {'match': match})
    else:
        errors = form.errors
        return HttpResponse("Error: %s" % str(errors))
    