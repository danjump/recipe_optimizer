from recipe_scraper import *
import timer
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver import ActionChains

#https://www.google.com/search?q=site%3Aallrecipes.com+%22chicken+salad%22
#&oq=site%3Aallrecipes.com+%22chicken+salad%22

#updating class to use driver
class google_search:
	"""this class is used to control
	a google search object, which is powered by a 
	selenium webdriver"""
	page_max = 100
	def __init__(self,website,query,max_results = 500):
		self.base_url = google_search_url(website,query)
		self.url = self.base_url
		self.max_results = max_results
		self.max_pages = math.ceil(max_results/100.)
		self.page_number = 1
		self.results_list = []
		self.timer = timer.timer(mean = 3.13,sd = 0.62, floor = 15.12, ceiling = 46.1)
		self.website = website
		self.query = query
		self.driver = setup_google_driver()
		self.open_first_url()
		time.sleep(1)
		self.terminated = False
	def get_info(self):
		print "Page: " + str(self.page_number)
	def can_continue(self):
		return not self.terminated
	def at_page_limit(self):
		return self.point_on_page == google_search.page_max
	def open_first_url(self):
		searchbar = self.driver.find_element_by_name('q')
		searchbar.send_keys("site:" + self.website +' "' + self.query + '"')
		searchbar.send_keys(Keys.ENTER)
		self.get_page_info()
	def get_page_info(self):
		html = self.driver.page_source
		self.soup = BeautifulSoup(html)
		results_list = self.soup.find_all('h3',{'class':'r'})
		self.results_list += [x.find('a').attrs['href'] for x in results_list]	
	def move_cursor(self):
		last_check = self.check_if_end()
		if last_check:
			self.terminated = True
		else:
			next_button = self.driver.find_element_by_id('pnnext')
			next_button.click()
			self.get_page_info()
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
	def loop_until_complete(self):
		while not self.terminated:
			self.get_info()
			print 'SLEEP: ' + str(self.timer.get_time_remaining())
			while not self.timer.check_time():
				pass
			self.move_cursor()
			self.page_number += 1
			if self.page_number > self.max_pages:
				self.terminated = True
		self.driver.quit()


def sptp(query):
	return re.sub(' ','+',query)

def google_search_url(website,query):
	query = sptp(query)
	return 'http://www.google.com/search?q=site:' + website + '+"' + query + '"' + '&num=100'

def setup_google_driver():
	driver = webdriver.Firefox()
	driver.get('http://google.com')
	time.sleep(0.2)
	#driver.maximize_window()
	time.sleep(3)
	driver.get('http://google.com/preferences')
	time.sleep(2)
	radios = driver.find_elements_by_css_selector('div.jfk-radiobutton')
	radio = radios[-1]
	radio.click()
	time.sleep(1.2)
	slider = driver.find_element_by_css_selector('div.goog-slider-scale')
	dims = slider.size
	width = dims['width']
	move = ActionChains(driver)
	slider2 = driver.find_element_by_css_selector('div.goog-slider-scale')
	for i in range(4):
		time.sleep(0.1)
		move.click_and_hold(slider2).move_by_offset(width//9,0).release().perform()
	move.click_and_hold(slider2).move_by_offset(width//2,0).release().perform()
	time.sleep(1.5)
	driver.switch_to_default_content()
	#save settings
	elems = driver.find_elements_by_id('form-buttons')
	elems[0].find_elements_by_tag_name('div')[0].click()
	alert = driver.switch_to_alert()
	time.sleep(0.91)
	alert.accept()
	time.sleep(1)
	return driver