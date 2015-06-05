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

def main(args):

        #Set our allrecipes search result url. in this case we are searching for hummus recipes
        search_results_url='http://allrecipes.com/search/default.aspx?qt=k&wt=hummus&rt=r&origin=Home%20Page'
        #create browser
	br=create_browser()

        #get list of recipe url's from search results
        results_list = read_search_results(search_results_url,br)

        #read info from all the recipe pages in to a dict
        recipe_info_dict = read_recipe_pages(results_list,br)

        
def read_search_results(search_results_url,br):
        """
        read a page containing recipe search results and extract the link to
        each recipe to return in a list.
        ------------------------
        input: (string containing a url of recipe search results,browser object)
        output: list of strings containing urls of individual recipes
        """
        
        #loop through a known 5 pages of search results
        results_list=[]
        for i in range(1,6):
                url=search_results_url+"&Page="+str(i)
                #Open the page and get the html content:
                html = br.open(url).read()
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

        return results_list
        
        
def read_recipe_pages(results_list,br):
        """
        input: list of recipe urls
        output: dictionary of dictionaries of info for each recipe
        """
        info = dict()
        for url in results_list:
                info[str(url)] = read_recipe_page(url,br)

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
        info['rating'] = allrecipes.get_rating(soup)
        info['votes'] = allrecipes.get_number_of_ratings(soup)
        info['yield'] = allrecipes.get_recipe_yield(soup)

        return info



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


if __name__=='__main__':
	main(sys.argv[1:])
