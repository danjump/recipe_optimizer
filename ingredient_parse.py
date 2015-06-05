import re

test_cases = ['2 cups canned garbanzo beans, drained','2 cloves garlic, halved',
	      '1/3 cup tahini','1/4 cup lemon juice','1 teaspoon salt',
	      '1 pinch paprika','1 tablespoon olive oil','1 teaspoon minced fresh parsely',
	      '1 clove garlic','1 (19 ounce) can garbanzo beans, half the liquid reserved',
	      '4 tablespoons lemon juice','1 cup garbanzo beans','1/3 cup canned jalepeno pepper slices, juice reserved',
	      '1/2 teaspoon curry powder','1/2 teaspoon ground cumin','crushed red pepper to taste',
	      '1 (15.5 ounce) can garbanzo beans (chickpeas), drained','1/3 cup pitted Spanish Manzanilla olives',
	      '1 1/2 teaspoons chopped fresh basil','salt and pepper to taste',
	      '1 teaspoon cilantro leaves','1 cup cooked chickpeas',
	      '2 cloves garlic, finely chopped','3/4 teaspoon ground cumin',
	      '1/4 cup water','2 tablespoons chopped fresh parsely, or to taste',
	      '1/2 cup tahini','2 (15 ounce) cans garbanzo beans, drained',
	      '1/4 cup crumbled feta cheese','1/4 cup sweet chili sauce',
	      '1 tablespoon water, or as needed (optional)','15 pitted kalamata olives',
	      '2 teaspoons dried dill weed','1 cup non-fat cottage cheese',
	      '1 pint grape tomatoes, coarsely chopped','1 (15.5 ounce) can cannellini beans',
	      '1 bunch fresh basil, chopped','ground black pepper to taste',
	      '1 teaspoon grated lemon zest, minced']

measures_by_weight = ['lb','(?<=!fluid )ounce','kilogram','gram','pound']
measures_by_volume = ['tablespoon','teaspoon','cup','quart','gallon',
		      'liter','milliliter','pinch','dash','pint','dessertspoon',
		      'drop','fluid ounce']
measures_by_quantity = ['clove','head','stalk','can','tin','container','box','slice','patty',
			'carton','stick','bottle']

measures_list = [measures_by_weight,measures_by_volume,measures_by_quantity]

numeral_regex = r'[0-9\.]+ ?/?[0-9]*/?[0-9]*'

def rfind(regex,text):
	"""faster version of verifying matches"""
	return None <> re.search(regex,text)

#fixes grammar issues with certain measures
def resolve_regex(text):
	return re.sub('hs?','h(es)?',text)

def try_regexes(part1,part2,part3,text):
	tlist = type([])
	if type(part1) <> tlist:
		part1 = [part1]
	if type(part2) <> tlist:
		part2 = [part2]
	if type(part3) <> tlist:
		part3 = [part3]
	"""tries a series of regular expressions so that
	if there are multiple lists to be tested from, they
	can be done iteratively"""
	for p1 in part1:
		for p2 in part2:
			for p3 in part3:
				if rfind(resolve_regex(p1+p2+p3),text):
					return [p1,p2,p3]
	return None

def try_regexes_nested(part1,part2list,part3,text,return_vals):
	for i in range(len(part2list)):
		part2 = part2list[i]
		rpattern = try_regexes(part1,part2,part3,text)
		if rpattern <> None:
			break
	if rpattern == None:
		return [None,return_vals[i+1]]
	else:
		return [rpattern,return_vals[i]]

def fraction_to_decimal(text):
	"""takes both regular and mixed fractions and converts them to float values"""
	if rfind(' ',text):
		splittext = text.split(' ')
		return float(splittext[0]) + float(fraction_to_decimal(splittext[1]))
	splittext = text.split('/')
	return float(splittext[0])/float(splittext[1])

def preprocess_quantity(text):
	"""converts some common english quantities to
	numerals and removes parenthesized text
	as well as padded embellishment"""
	text = re.sub('dozen','12 ',text)
	text = re.sub('^one ','1 ',text)
	text = re.sub('^two ','2 ',text)
	text = re.sub('^three ','3 ',text)
	text = re.sub('^four ','4 ',text)
	text = re.sub('a pair of','2',text)
	text = re.sub(' of','',text)
	text = re.sub(', .*$','',text)
	text = re.sub(r'\(.+?\)','',text)
	text = re.sub('  ',' ',text)
	text = re.sub(',? to taste','',text)
	return text

def extract_quantity(text):
	measure_classes = ['weight','volume','quantity','raw']
	rpattern = try_regexes_nested(numeral_regex,measures_list,'s?',text,
			       measure_classes)
	nump= re.search(numeral_regex,text)
	if nump == None:
		print 'cannot find quantity for: ' + text
		return [1.,'err','raw',text]
	numb = nump.group(0)
	if rfind('/',numb):
		numb = fraction_to_decimal(numb)
	else:
		numb = float(numb)
	if rpattern[0] == None:
		text = re.sub('^ ?','',text)
		return [numb,'raw','raw',text]
	else:
		text = re.sub(rpattern[0][0] + rpattern[0][1] + rpattern[0][2] + ' ?','',text)
		text = re.sub('[^a-zA-Z \-]+','',text)
	return [numb,rpattern[0][1],rpattern[1],text]
	
def extract_embellishment(text):
	embellisher_search = re.search(', .*$',text)
	if embellisher_search <> None:
		embellish = embellisher_search.group(0)[2:]
	else:
		embellish = None
	return embellish
	

def parse_ingredient(text):
	embellishment = extract_embellishment(text)
	text = preprocess_quantity(text)
	quantities_data = extract_quantity(text)
	return [quantities_data,embellishment]
	
	

