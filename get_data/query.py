import * from recipe
import * from timer

class query:
	def __init__(self,query,website):
		self.query = query
		self.website = website
		self.default_url = ''
		self.url_list = []
		self.browser = recipe.create_browser()
		self.npages = -1
		self.current_page = 0
		self.started = False
		self.finished = False
	def url_list(self):
		return self.url_list
	def proceed(self):
		self.finished = self.check_if_finished()
		if not self.finished:
			self.next_page()
	def extract_urls(self):
		self.start()
		while not self.finished:
			self.get_urls()
			self.proceed()
			print "FINISHED EXTRACTING URLS"
			
			