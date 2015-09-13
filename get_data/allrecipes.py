from recipe_scraper import *
import recipe
import time
from recipe import *
from query import *

class recipe.recipe(allrecipes):
	def generate_data(self):
		self.fix_url()
		self.load_page()
		self.get_rating()
		self.get_recipe_yield()
		self.get_number_of_ratings()
		self.generate_ingredients_dict()
		self.get_recipe_times()
		self.get_instructions()
	def load_page(self):
		while True:
			try:
				html = self.browser.open.read(self.url)
				self.soup = BeautifulSoup(html)
				self.timestamp = str(datetime.datetime.now()).split('.')[0]
				break
			except ConnectionError:
				print "cannot connect...sleeping for 10 seconds"
				time.sleep(10)
		print "loaded " + self.url
	def get_rating(self):
		"""average rating"""
		obj = self.soup.find_all('meta',{'itemprop':'ratingValue'})[0]
		self.averageRating = float(obj.get('content'))
	def get_recipe_yield(self):
		obj = self.soup.find('span',{'id':'lblYield'})
		self.recipeYield = str(obj.text)
	def get_number_of_ratings(self):
		obj = self.soup.find('p',{'id':'pRatings'})
		text = str(obj.text)
		text = re.sub('[^0-9]+','',text)
		self.numberRatings = int(text)
	def generate_ingredients_dict(self):
		ingredient_frame = self.soup.find_all('li',{'id':'liIngredient'})
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
			#e.g., sauces, general components
			if ingredient_index == "0":
				continue
			description = removeNonAscii(obj.find('span',{'class':'ingredient-name'}).text)
			grams = float(obj.get('data-grams'))
			amount = obj.get('ingredient-amount')
			ingredient['description'] = description
			ingredient['grams'] = grams
			ingredient['amount'] = amount
			ingredients[ingredient_index] = ingredient
		self.ingredients = ingredients
	def get_recipe_times(self):
		prep_time = 0
		prep_mins = self.soup.find('span',{'id':'prepMinsSpan'})
		if prep_mins <> None:
			prep_time += int(prep_mins.find('em'))
		prep_hours = soup.find('span',{'id':'prepHoursSpan'})
		if prep_hours <> None:
			prep_time += 60*int(prep_hours.find('em')
		cook_time = 0
		cook_mins =self.soup.find('span',{'id':'cookMinsSpan'})
		if cook_mins <> None:
			cook_time += int(cook_mins.find('em'))
		cook_hours = self.soup.find('span',{'id':'cookHoursSpan'})
		if cook_hours <> None:
			cook_time += 60 * int(cook_hours.find('em'))
		ready_time = 0
		ready_mins = self.soup.find('span',{'id':'totalMinsSpan'})
		if ready_mins <> None:
			ready_time += int(ready_mins.find('em'))
		ready_hours = self.soup.find('span',{'id','totalHoursSpan'})
		if ready_hours <> None:
			ready_hours += 60* int(ready_hours.find('em'))
		self.activePrepTime = prep_time
		self.cookTime = cook_time
		self.totalTime = ready_time
	def get_instructions(self):
		directions = soup.find('div',{'itemprop':'recipeInstructions'})
		directions = directions.find('ol')
		dlist = directions.find_all('li')
		for item in dlist:
			text = item.find('span').text
			self.instructions.append(text)
	def fix_url(self):
		"""ensures that url refers to full version of allrecipes (will fail otherwise)"""
		if re.search('\?sitepref=ar',self.url) == None:
			self.url += '?sitepref=ar'
	
class allrecipesQuery:
	


#supporter functions
def removeNonAscii(text):
	return ''.join([x for x in text if ord(x) < 128])

def get_index_or_none(obj,i):
	if obj[i] == None:
		return ''
	else:
		return str(removeNonAscii(obj[i].text))

def validate_url(url):
	"""validates whether or not a url from allrecipes.com is a 
	recipe"""
	return re.search('/recipe/[^/]+/$',url) <> None