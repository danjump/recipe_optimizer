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
#functions from this file are called with allrecipes.funcname
import "allrecipes"

def main(args):

        #Set our allrecipes search result url. in this case we are searching for hummus recipes
        search_results_page='http://allrecipes.com/search/default.aspx?qt=k&wt=hummus&rt=r&origin=Home%20Page'

        #get list of recipe url's from search results
        results_list = read_search_results(search_results_page)

        print(results_list)

        
def read_search_results(search_results_page):
        """
        input: string containing a url of recipe search results
        output: list of strings containing urls of individual recipes
        """
        #create browser
	br=create_browser()
        
        #loop through a known 5 pages of search results
        results_list=[]
        for i in range(1,6):
                page=search_results_page+"&Page="+str(i)
                #Open the page and get the html content:
                html = br.open(page).read()
                #feed in to beautifulsoup
                soup = BeautifulSoup(html)
                #get a frame for each recipe
                frames = soup.find_all("a",{"class":"title"})
                
                #loop through the frames to get urls ad add them to the results list
                for frame in frames:
                        url_suffix=frame['href']
                        full_url='http://allrecipes.com'+url_suffix
                        results_list.append(full_url)

                time.sleep(8)
        
        return results_list
                


def create_browser():
	#currently the one I use, but it should work
	user_agent="Opera/9.80 (Windows NT 6.1; Win64; x64) Presto/2.12.388 Version/12.16"

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
