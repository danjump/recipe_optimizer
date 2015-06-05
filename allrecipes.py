def get_rating(soup):
	obj = soup.find_all('meta',{'itemprop':'ratingValue'})[0]
	return float(obj.get('content'))

def get_recipe_yield(soup):
	obj = soup.find('span',{'id':'lblYield'))
	return str(obj.text)

def get_number_of_ratings(soup):
	obj = soup.find('p',{'id':'pRatings'})
	text = str(obj.text)
	text = re.sub('[^0-9]+','',text)
	val = int(text)
	return val