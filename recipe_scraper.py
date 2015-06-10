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
import allrecipes
import ingredient_parse
import google_search
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver import ActionChains
import timer

MAX_SEARCH_ENTRIES = 500

def main(args):
	#these will be default until command-line arguments are supported
	query = 'chicken'
	website = 'allrecipes.com'
        #Set our allrecipes search result url. in this case we are searching for hummus recipes
        search_results_url='http://allrecipes.com/search/default.aspx?qt=k&wt='+query+'&rt=r&origin=Home%20Page'
        #create browser
	br=create_browser()
	
	gs = google_search.google_search(website,query,200)
	
	gs.loop_until_complete()
	results_list = gs.results_list
	results_list = [x for x in results_list if allrecipes.validate_url(x)]
        #get list of recipe url's from search results
        if False:
		results_list = read_search_results(search_results_url,br)
	print "READING INFO FROM RECIPE PAGES"
        #read info from all the recipe pages in to a dict
        recipe_info_dict = read_recipe_pages(results_list,br,query)

        write_info_to_database(recipe_info_dict)

        
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


#this may be obsolete with the addition of google stuff
#but I'll keep it here for now
def read_search_results(search_results_url,br):
        """
        read a page containing recipe search results and extract the link to
        each recipe to return in a list.
        ------------------------
        input: (string containing a url of recipe search results,browser object)
        output: list of strings containing urls of individual recipes
        """
        
        #loop through a known 5 pages of search results
        npages=5
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
        for count, url in enumerate(results_list):
                print 'Reading recipe '+str(count+1)+' of '+str(len(results_list))
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
		recipe_id INTEGER, 
		search_query TEXT,
		url TEXT,
		website TEXT,
		timestamp TEXT,
		average_rating REAL,
		number_ratings INTEGER,
		yield_quantity REAL,
		yield_units TEXT,
		yield_type TEXT,
		PRIMARY KEY (recipe_id,url)
		);""")
	c.execute("""CREATE TABLE IF NOT EXISTS ingredients(
		recipe_id INTEGER,
                ingredient_id INTEGER,
		description TEXT,
		amount REAL
		);""")
	c.execute("""SELECT count(*) from recipes;""")
	n = c.fetchall()[0][0]
	#avoids duplicate urls from being added
	c.execute("""SELECT url from recipes;""")
	url_list = c.fetchall()
	url_list = [x[0] for x in url_list]
	#it is faster to execute all the commands as a single sql command
	#than to use `c.execute_many` because of the minimum amount of time commands
	#connections take to execute
	recipelist = []
	ingredientlist = []
	for key in info:
		entry = info[key]
		url = key
		if url in url_list:
			print "AVOIDING DUPLICATE URL: " + url
			continue
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
	if len(recipelist) > 0:
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
