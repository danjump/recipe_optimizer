from recipe_scraper import *

def get_rating(soup):
	obj = soup.find_all('meta',{'itemprop':'ratingValue'})[0]
	return float(obj.get('content'))

def get_recipe_yield(soup):
	obj = soup.find('span',{'id':'lblYield'})
	return str(obj.text)

def get_number_of_ratings(soup):
	obj = soup.find('p',{'id':'pRatings'})
	text = str(obj.text)
	text = re.sub('[^0-9]+','',text)
	val = int(text)
	return val

def removeNonAscii(text):
	return ''.join([x for x in text if ord(x) < 128])

def get_index_or_none(obj,i):
	if obj[i] == None:
		return ''
	else:
		return str(removeNonAscii(obj[i].text))

def get_ingredients(soup):
	ingredients = soup.find_all('li',{'id':'liIngredient'})
	amounts = [obj.find('span',{'class':'ingredient-amount'}) for obj in ingredients]
	names = [obj.find('span',{'class':'ingredient-name'}) for obj in ingredients]
	nIngredients = len(amounts)
	try:
		ipairs = [[get_index_or_none(amounts,i),get_index_or_none(names,i)] for i in range(nIngredients)]
	except AttributeError:
		print ingredients
		print '+++'
		print amounts
		print names
		raise
	return ipairs