from recipe_scraper import *

#https://www.google.com/search?q=site%3Aallrecipes.com+%22chicken+salad%22
#&oq=site%3Aallrecipes.com+%22chicken+salad%22

class google_search:
	page_max = 10
	def __init__(self,website,query,browser):
		self.base_url = google_search_url(website,query)
		self.url = self.base_url
		self.page_number = 1
		self.website = website
		self.query = query
		self.n = 1
		self.point_on_page = 1
		self.browser = browser
		self.open_url()
		self.terminated = False
	def can_continue(self):
		return not self.terminated
	def open_url(self):
		page = self.browser.open(self.url)
		html = page.read()
		self.soup = BeautifulSoup(html)
		self.results_list = self.soup.find_all('h3',{'class':'r'})
	def get_current_entry(self):
		if self.terminated:
			print "ERROR: NO MORE SEARCH RESULTS"
			return None
		else:
			result = self.results_list[self.point_on_page-1].find('a').attrs['href']
			self.move_cursor()
			return result	
	def move_cursor(self):
		if not self.terminated:
			self.n += 1
		if self.point_on_page == google_search.page_max:
			last_check = self.check_if_end()
			if last_check:
				self.terminated = True
			else:
				self.page_number += 1
				self.point_on_page = 1
				self.url = self.base_url + '&start=' + str(10*(self.page_number-1))
				self.open_url()
		elif self.check_page_position():
			self.point_on_page += 1
		else:
			self.terminated = True
	def check_page_position(self):
		if len(self.results_list) < google_search.page_max & len(self.results_list) == self.point_on_page:
			return False
		return True
	def check_if_end(self):
		#first check
		obj = self.soup.find_all('td',{'class':'b navend'})
		if obj == None or len(obj) < 2:
			return True
		obj2 = obj[1].find('a')
		if obj2 == None:
			return True
		if 'href' not in obj2.attrs:
			return True
		return False


def sptp(query):
	return re.sub(' ','+',query)

def google_search_url(website,query):
	query = sptp(query)
	return 'http://www.google.com/search?q=site:' + website + '+"' + query + '"'
