import re
from bs4 import BeautifulSoup
import cookielib
import datetime
import mechanize
import time
import math

class recipe:
	"""this class holds a recipe so that it can be easily written to disk"""
	def __init__(self, url, query,browser):
		self.browser = browser
		self.url = url
		#contains page info
		self.soup = None
		self.extract_website()
		#dictionary format
		#{ingredient_id,ingredient_name,grams,text_amount}
		#note: as long as future methods treat this as an iterable, it doesn't matter
		#if it's a list or dict
		self.ingredients = dict()
		#each step in text format; will not be used for analysis unti much later
		self.instructions = []
		self.activePrepTime = -1
		self.cookTime = -1
		self.totalTime = -1
		self.dateAcquired = -1
		self.numberRatings = -1
		self.averageRating = -1
		self.query = query
		self.recipeYield = None
		self.timestamp = None
	def extract_website(self):
		"""currently assumes .com website; I don't think we'll use any others"""
		self.website = re.sub('http://(www\.)?|(?<=\.com)/.*$','',self.url)
	def write_to_database(self,dbname = 'recipes.db'):
		conn = sqlite3.connect('../' + dbname)
		c = conn.cursor()
		#create master table of recipes
		c.execute("""CREATE TABLE IF NOT EXISTS recipes(
			recipe_id INTEGER,
			search_query TEXT,
			url TEXT,
			website TEXT,
			timestamp TEXT,
			average_rating REAL,
			number_ratings INTEGER,
			yield_units TEXT,
			yield_type TEXT,
			active_prep_time INTEGER,
			cook_time INTEGER,
			total_time INTEGER,
			PRIMARY KEY (recipe_id, url);""")
		#create ingredient table for recipes
		c.execute("""CREATE TABLE IF NOT EXISTS ingredients(
			recipe_id INTEGER,
			ingredient_id INTEGER,
			description TEXT,
			amount REAL,
			is_standardized INTEGER);""")
		#creates table for storing instructions
		c.execute("""CREATE TABLE IF NOT EXISTS instructions(
			recipe_id INTEGER,
			step_number INTEGER,
			step_text TEXT)""")
		
		#check to see if recipe is already in database 
		#query and url must be both matched to count
		c.execute("""SELECT count(*) from recipes
			WHERE url = %s AND search_query = %s;""" % (self.url,self.query))
		count = c.fetchall()[0]
		if count <> 0:
			print "URL %s for QUERY %s already in database" % (self.url,self.query)
			return
		c.execute("""SELECT count(*) from recipes LIMIT 1;""")
		count = c.fetchall()[0]
		if count <> 0:
			c.execute("""SELECT max(recipe_id) from recipes;""")
			new_id = c.fetchall()[0]
		else:
			new_id = 0
		rlist = [new_id,self.query,self.url,self.website,self.timestamp,self.averageRating,
	   self.numberRatings, self.yield_units,'unspecified',self.activePrepTime,self.cookTime,
	   self.totalTime]
		c.executemany("""INSERT INTO recipes VALUES(?,?,?,?,?,?,?,?,?,?,?,?);""",rlist)
		ilist = []
		for ing in self.ingredients:
			ingr = self.ingredients[ing]
			ilist.append([new_id,ing,ingr['grams'],ingr['description'],ingr['amount'],0])
		c.executemany("""INSERT INTO ingredients VALUES(?,?,?,?,?);""",ilist)
		slist = [[new_id,a,obj] for a,obj in enumerate(self.ingredients)]
		c.executemany("""INSERT INTO descriptions VALUES(?,?,?);""",slist)
		c.close()
		conn.close()
		print "DONE WITH %s" % self.url

def extract_website(url):
	"""this method is defined here so that the recipe object can be cast as the correct
	subclass the first time it is created"""
	return re.sub('http://(www\.)?|(?<=\.com)/.*$','',url)

 
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