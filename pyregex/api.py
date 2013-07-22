import webapp2
import json
from .decorators import handle_json
import sys
import logging

class ApiBaseResource(webapp2.RequestHandler):
	pass


class RegexResource(ApiBaseResource):
	__urls__ = ('regex/', 'regex/<key>')

	@handle_json
	def get(self):
		return {'hello': 'world'}
