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

def generate_ingredients_dict(soup):
	ingredient_frame = soup.find_all('li',{'id':'liIngredient'})
 
        #this will be a dictionary with entries that are dictionaries.
        #the sub-dictionaries will have entries for the description and
        #amount of each ingredient
        ingredients = dict()

        #loop though each ingredient in the recipe
        for obj in ingredient_frame:
                ingredient = dict()

                #this is an index value used by allrecipes.com for each ingredient
                ingredient_index = int(obj.get('data-ingredientid'))
                #happens if there are multiple groups of large ingredients
                #e.g., sauces
                if ingredient_index == "0":
			continue
	        description = removeNonAscii(obj.find('span',{'class':'ingredient-name'}).text)
                amount = float(obj.get('data-grams'))

                ingredient['description'] = description
                ingredient['amount'] = amount

                ingredients[ingredient_index] = ingredient
	
        return ingredients

def validate_url(url):
	return re.search('/recipe/[^/]+/$',url) <> None