import mechanize
import cookielib
from bs4 import BeautifulSoup
import re
import os
import math
import sqlite3
import sys
import numpy
import time
import csv
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver import ActionChains
import timer


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
			self.get_page_info()
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

def create_browser():
        """
        this function is used to make it look like a real person is using a browser
        output: mechanize browser object
        """
	#currently the one I use, but it should work
	#user_agent="Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:38.0) Gecko/20100101 Firefox/38.0"
        user_agent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/41.0.2272.76 Chrome/41.0.2272.76 Safari/537.36"
        br=mechanize.Browser()
	#makes br behave like a real browser
	cj=cookielib.LWPCookieJar()
	br.set_cookiejar(cj)
	br.set_handle_equiv(True)
	br.set_handle_gzip(True)
	#temporarily changed to False due to unwanted mobile redirection
	br.set_handle_redirect(False)
	br.set_handle_referer(True)
	br.set_handle_robots(False)
	#debug messages if desired
	br.set_debug_http(False)
	br.set_debug_redirects(True)
	br.set_debug_responses(False)
	#adding user agent...this is kind of shady
	br.addheaders=[('User-agent',user_agent)]
	return br


#come up with way to store page data

def make_basic_chain_elements(terms,dnames,attrs,concatenate):
	return [[[terms[i],attrs[i],None],[dnames[i],concatenate[i]],None] for i in range(len(terms))]

def extract_chained_data(chain, soup,data):
	if chain==None:
		return [element.text for element in soup.find_all()]
	for item in chain:
		sp = item[0]
		dp = item[1]
		nc = item[2]
		element = soup.find_all(sp[0],sp[1],limit=sp[2])
		if dp <> None:
			objs = [e.text for e in element]
			if dp[1]:
				objs = [' '.join(objs)]
			if dp[0] not in data.keys():
				data[dp[0]] = objs
			else:
				data[dp[0]] = [data[dp[0]],objs]
		if nc <> None:
			data = extract_chained_data(nc,element,data)
	return data

def grab_url_info(url,br, bs4chain = None):
	"""bs4chain structure is as follows:
	[search_parameters (name
	,attrs,limit),
	dict parameter (name, concatenate?),
	[further_subchain]]
	"""
	html = br.open(url).read()
	soup = BeautifulSoup(html)
	data = extract_chained_data(bs4chain,soup,dict())
	return data	

def reset_database(dbname='test.db'):
	conn = sqlite3.connect(dbname)
	c = conn.cursor()
	c.execute("DROP TABLE data;")
	conn.commit()
	c.close()
	conn.close()
	return

def store_data_in_sql_database(query,url,data,dbname='test.db'):
	conn = sqlite3.connect(dbname)
	c = conn.cursor()
	c.execute("""CREATE TABLE IF NOT EXISTS data(
		query TEXT,
		url TEXT,
		site TEXT,
		varname TEXT,
		value TEXT);""")
	c.execute("""SELECT DISTINCT url FROM data;""")
	site = re.sub('https?://(www.?\.)','',url)
	site = re.sub('/.*','',site)
	queries = c.fetchall()
	if url in urls:
		print "ALREADY TRIED THIS QUERY: " + query
		return
	for var_entry in data:
		print var_entry
		to_insert = [[query,url,site,var_entry,e] for e in data[var_entry]]
		c.executemany("""INSERT INTO data VALUES(?,?,?,?,?);""",to_insert)
	conn.commit()
	c.close()
	conn.close()
	print "QUERY FINISHED: " + query
	
def perform_mass_scraping(sitelist,querylist,max_results,chainlist,validation_functions=None,dbname='test.db'):
	br = create_browser()
	if chainlist = None:
		chainlist = [make_basic_chain_elements('p','text',None,True) for i in range(len(sitelist))]
	i = 0
	new_timer = timer()
	for site in sitelist:
		for query in querylist:
			engine = google_search(site,query,max_results)
			engine.loop_until_complete()
			results_list = engine.results_list
			if validation_functions <> None:
				func = validation_functions[i]
				results_list = [o for o in results_list if func(o)]
			for url in results_list:
				data = grab_url_info(url,br,chainlist[i])
				store_data_in_sql_database(query,url,data,dbname)
				while not new_timer.check_time():
					pass		
		i+=1