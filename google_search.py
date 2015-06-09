import re

#https://www.google.com/search?q=site%3Aallrecipes.com+%22chicken+salad%22
#&oq=site%3Aallrecipes.com+%22chicken+salad%22

def sptp(query):
	return re.sub(' ','+',query)

def google_search_url(website,query):
	query = sptp(query)
	return 'http://www.google.com/search?q=site%3A' + website + 
	'%22' + query + '%22&oq=site%3A' + website + '%22' + query + 
	'%22'