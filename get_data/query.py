import * from recipe
import * from timer

class query:
	def __init__(self,query,website):
		self.query = query
		self.website = website
		self.url_list = []
		self.current_page = 0
		self.started = False
	def url_list(self):
		return self.url_list