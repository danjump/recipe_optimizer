import mechanize
import cookielib
from bs4 import BeautifulSoup
import re
import os
import sqlite3
import sys
import numpy
import time
import csv
import allrecipes
import ingredient_parse

class timer:
	"""this class creates a timer object
	that can be used to determine how frequently to scan something"""
	def generate_random_time(self):
		return self.floor + min(numpy.random.lognormal(self.mean,self.sd,1)[0],self.ceiling)
	def __init__(self,mean = 0.526,sd = 0.29,floor = 0.104014,ceiling = 4.307):
		self.origin = time.time()
		self.floor = floor
		self.mean = mean
		self.sd = sd
		self.ceiling = ceiling
		self.prev_time = self.origin
		self.next_counter = self.generate_random_time()
		self.nresets = 0
	def reset_time(self):
		self.prev_time = time.time()
		self.next_counter = self.generate_random_time()
	def check_time(self):
		"""this should be the only function used when
		running this normally"""
		if time.time() - self.next_counter > self.prev_time:
			self.reset_time()
			self.nresets += 1
			return True
		else:
			return False
	def get_number_resets(self):
		return self.nresets
	def get_time_remaining(self):
		return self.prev_time + self.next_counter - time.time()
	
def main(args):
	query = 'hummus'
        #Set our allrecipes search result url. in this case we are searching for hummus recipes
        search_results_url='http://allrecipes.com/search/default.aspx?qt=k&wt='+query+'&rt=r&origin=Home%20Page'
        #create browser
	br=create_browser()

        #get list of recipe url's from search results
        results_list = read_search_results(search_results_url,br)

        #read info from all the recipe pages in to a dict
        recipe_info_dict = read_recipe_pages(results_list,br,query)

        write_info_to_database(recipe_info_dict)

        
def create_browser():
        """
        this function is used to make it look like a real person is using a browser
        output: mechanize browser object
        """
	#currently the one I use, but it should work
	user_agent="Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:38.0) Gecko/20100101 Firefox/38.0"
        
        br=mechanize.Browser()
	#makes br behave like a real browser
	cj=cookielib.LWPCookieJar()
	br.set_cookiejar(cj)
	br.set_handle_equiv(True)
	br.set_handle_gzip(True)
	br.set_handle_redirect(True)
	br.set_handle_referer(True)
	br.set_handle_robots(False)
	#debug messages if desired
	br.set_debug_http(False)
	br.set_debug_redirects(True)
	br.set_debug_responses(False)
	#adding user agent...this is kind of shady
	br.addheaders=[('User-agent',user_agent)]
	
	return br


def read_search_results(search_results_url,br):
        """
        read a page containing recipe search results and extract the link to
        each recipe to return in a list.
        ------------------------
        input: (string containing a url of recipe search results,browser object)
        output: list of strings containing urls of individual recipes
        """
        
        #loop through a known 5 pages of search results
        npages=1
        results_list=[]
        for i in range(1,npages+1):
                url=search_results_url+"&Page="+str(i)
                #Open the page and get the html content:
                html = br.open(url).read()
                print "Reading Search Results Page #"+str(i)+" of "+str(npages)+":\n" + url
                time.sleep(numpy.random.lognormal(1,1,1))
                #feed in to beautifulsoup
                soup = BeautifulSoup(html)
                #get a frame for each recipe
                frames = soup.find_all("a",{"class":"title"})
                
                #loop through the frames to get urls ad add them to the results list
                for frame in frames:
                        url_suffix=frame['href']
                        full_url='http://allrecipes.com'+url_suffix
                        results_list.append(full_url)

        print('\nFinished reading search results! Found '+str(len(results_list))+' recipes\n\n')
        return results_list
        
        
def read_recipe_pages(results_list,br,query):
        """
        input: list of recipe urls
        output: dictionary of dictionaries of info for each recipe
        """
        info = dict()
        count=1
        for url in results_list:
                print 'Reading recipe '+str(count)+' of '+str(len(results_list))
                count+=1
		print 'URL: ' + url
                info[str(url)] = read_recipe_page(url,br)
                info[str(url)]['query'] = query

        return info


def read_recipe_page(url,br):
        """
        input: url to a recipe
        output: dictionary of info for each recipe
        """
        #Open the page and get the html content:
        html = br.open(url).read()
        time.sleep(numpy.random.lognormal(1,1,1))
        #feed in to beautifulsoup
        soup = BeautifulSoup(html)
        
        info = dict()
        #set entries with one value:
        info['rating'] = allrecipes.get_rating(soup)
        info['votes'] = allrecipes.get_number_of_ratings(soup)
        info['yield'] = allrecipes.get_recipe_yield(soup)
        info['timestamp'] = time.strftime('%Y-%m-%d %H:%M:%S')
	#this entry points to a sub dict with entries for each ingredient
        #which in turn points to a sub dict that has a 'name' and 'amount'
        #entry for each ingredient:
        info['ingredients'] = allrecipes.generate_ingredients_dict(soup)
        return info

def write_info_to_database(info):
	"""stores info extracted to pages to a sqlite database"""
	conn = sqlite3.connect('recipes.db')
	c = conn.cursor()
	c.execute("""CREATE TABLE IF NOT EXISTS recipes(
		recipe_id INTEGER PRIMARY KEY, 
		search_query TEXT,
		url TEXT,
		website TEXT,
		timestamp TEXT,
		average_rating REAL,
		number_ratings INTEGER,
		yield_quantity REAL,
		yield_units TEXT,
		yield_type TEXT
		);""")
	c.execute("""CREATE TABLE IF NOT EXISTS ingredients(
		recipe_id INTEGER,
                ingredient_id INTEGER,
		description TEXT,
		amount REAL
		);""")
	c.execute("""SELECT count(*) from recipes;""")
	n = c.fetchall()[0][0]
	#it is faster to execute all the commands as a single sql command
	#than to use `c.execute_many` because of the minimum amount of time commands
	#connections take to execute
	recipelist = []
	ingredientlist = []
	for key in info:
		entry = info[key]
		url = key
		website = re.search('(?<=http://).+?(?=/)',url).group(0)
		ingparse = ingredient_parse.parse_ingredient(entry['yield'])
		recipelist.append([n,entry['query'],url,website,
		     entry['timestamp'],entry['rating'],entry['votes'],
		     float(ingparse[0][0]),ingparse[0][1],ingparse[0][2]])
		ingredients = entry['ingredients']
                #here the key value of each ingredient entry in ingredients
                #is the allrecipes id # for each ingredient
		for ing_id in ingredients.keys():
                        ing = ingredients[ing_id]
			ingredientlist.append([n,ing_id,ing['description'],
			  ing['amount']])
		n+=1
	
	c.executemany("""INSERT INTO recipes VALUES(?,?,?,?,?,?,?,?,?,?);""",
	       recipelist)
	c.executemany("""INSERT INTO ingredients VALUES(?,?,?,?);""",
	       ingredientlist)
	c.execute("""SELECT COUNT(*) FROM recipes""")
	nrecipes = c.fetchall()[0][0]
	c.execute("""SELECT COUNT(*) FROM ingredients""")
	ningredients = c.fetchall()[0][0]
	conn.commit()
	print "TOTAL RECIPES: " + str(nrecipes)
	print "TOTAL INGREDIENTS: " + str(ningredients)
	c.close()
	conn.close()


if __name__=='__main__':
	main(sys.argv[1:])
