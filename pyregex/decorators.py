import json

def handle_json(cb):
	def req_handler(self, *args, **kwargs):
		result = cb(self, *args, **kwargs)
		if hasattr(result, '__getitem__') and hasattr(result, '__setitem__'):
			self.response.headers['Content-type'] = 'application/json'
			self.response.write(json.dumps(result))
	return req_handler