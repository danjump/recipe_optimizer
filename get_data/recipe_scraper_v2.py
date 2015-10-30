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

MAX_SEARCH_ENTRIES = 1000





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