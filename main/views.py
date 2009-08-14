from django.shortcuts import render_to_response
from django.template import RequestContext

def index(req):
    return render_to_response("main/index.html", RequestContext({}))
