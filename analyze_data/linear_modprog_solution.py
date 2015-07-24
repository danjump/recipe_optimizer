#creates numpy array
import sqlite3
import scipy
import sklearn
import numpy
from sklearn import linear_model
from sklearn.linear_model import LassoLarsIC
import re
import os
import sys
import math
import copy

#todo:

#create a table of new ingredient ids to correspond to new indices, where
#0=other ingredients, 1, 2, 3, etc. refer to all other ingredients

#output this new table to python

def main(args):
	"""doesn't really need to exist, but can be modified if needed;
	demonstrates how to use functions in context of analysis"""
	return
	query = 'hummus'
	data = get_model_data(query)
	data = apply_response_function(data)
	data = require_ingredient_bounds(data,'chickpeas',[0.2,1])
	xvar = data[0]
	yvar = data[1]
	#as long as no cuts are made to response value
	#an intercept would be redundant since sum(proportions)=1
	model = LassoLarsIC(criterion='aic',fit_intercept = False)
	model.fit(xvar,yvar)
	params = model.coef_
	sol = solve_linear_programming(data[0],model)
	v = sol.values()
	print numpy.column_stack((data[3],v[4]))

#may want to move function to other file later
def read_data(query,cutoff = 5):
	"""reads in the data from the sql database
	note that recipe ID and ingredient ID are set from ranges 
	[0, k] and [0,N], where k and N are the number of distinct
	ingredients and recipes (after making cuts to arcane ingredients)
	"""
	#
	if type(query) <> type('hi'):
		print "QUERY NEEDS TO BE A STRING"
		raise TypeError
	if type(cutoff) <> type(1):
		print "CUTOFF NEEDS TO BE AN INTEGER"
		raise TypeError
	if re.search('[^a-zA-Z0-9 ]',query) <> None:
		print 'INVALID QUERY, POSSIBLE INJECTION ATTEMPT'
		raise 
	os.chdir('/home/max/workspace/recipe_optimizer')
	conn = sqlite3.connect('recipes.db')
	c = conn.cursor()
	c.execute("""CREATE TEMP TABLE temptable AS SELECT 
		fr.recipe_id AS recipe_id,ingredient_id, amount,
		yield_quantity,description,-1 AS idx
		FROM (SELECT 
		CASE
		WHEN summary.total < %s THEN 0
		ELSE ingredients.ingredient_id
		END AS ingredient_id,
		recipe_id, description,amount
		FROM ingredients,
		(SELECT ingredient_id,count(ingredient_id) AS total 
		FROM ingredients, 
		(SELECT * FROM recipes WHERE search_query='%s') r 
		WHERE ingredients.recipe_id=r.recipe_id  
		GROUP BY ingredient_id 
		ORDER BY count(*)) summary
		WHERE summary.ingredient_id = ingredients.ingredient_id) fr
		INNER JOIN (SELECT 
		recipe_id,SUM(amount) AS yield_quantity FROM ingredients
		GROUP BY recipe_id) sr
		ON fr.recipe_id = sr.recipe_id;""" % (cutoff,query))
	c.execute("""UPDATE temptable SET idx=
		(SELECT count(*) FROM 
		(SELECT DISTINCT ingredient_id AS ingredient_id
		FROM temptable AS tt) tt2
		WHERE temptable.ingredient_id > tt2.ingredient_id
		);""")
	c.execute("""UPDATE temptable SET recipe_id=
		(SELECT count(*) FROM 
		(SELECT DISTINCT recipe_id AS recipe_id
		FROM temptable AS tt) tt2
		WHERE temptable.recipe_id > tt2.recipe_id
		);""")
	c.execute("""SELECT recipe_id,ingredient_id,amount,yield_quantity
		, description, idx FROM temptable 
		ORDER BY recipe_id, ingredient_id;""")
	data = c.fetchall()
	c.execute("""SELECT DISTINCT idx,description 
		FROM temptable
		WHERE idx <> 0
		ORDER BY idx,length(description);""")
	ilabels = c.fetchall()
	ilabels = fix_ingredient_labels(ilabels)
	c.close()
	conn.close()
	return [data,ilabels]

#very rough solution
def fix_ingredient_labels(labels):
	"""a cheap hack that defines an ingredient's label based on
	the shortest one with a shared recipe ID"""
	descriptions = []
	pv = -1
	for label in labels:
		if label[0] <> pv:
			descriptions.append(label[1])
			pv = label[0]
	return descriptions

def extract_rating_data(query):
	"""returns the recipe IDs, number of ratings, and average rating
	of recipes from a query"""
	conn = sqlite3.connect('recipes.db')
	c = conn.cursor()
	c.execute("""CREATE TEMP TABLE qtable AS
		SELECT average_rating, number_ratings,
		recipe_id, yield_quantity 
		FROM recipes
		WHERE search_query = '%s';""" % (query))
	c.execute("""CREATE TEMP TABLE rtable AS
		SELECT average_rating, number_ratings, 
		recipe_id FROM qtable;""")
		
	c.execute("""UPDATE rtable SET recipe_id=
		(SELECT count(*) FROM 
		(SELECT  recipe_id AS recipe_id
		FROM rtable AS rt) rt2
		WHERE rtable.recipe_id > rt2.recipe_id
		);""")
	c.execute("""SELECT recipe_id, number_ratings, average_rating 
		FROM rtable ORDER BY recipe_id;""")
	data = c.fetchall()
	c.close()
	conn.close()
	return data

def apply_response_function(data):
	"""wrapper to modify the y-value of `data`
	with response_function"""
	data[1] = response_function(data[1])
	return data

#objective function for recipes
def response_function(y):
	"""transforms number of ratings and total rating into a 
	response value"""
	return numpy.asarray([x[2]*math.log(1+x[1]) for x in y])

def get_model_data(query,cutoff=5,other_ingredient_cutoff=0,new_column_cutoff=0):
	"""Takes a query and  cutoff value for # of times an ingredient appears,
	returns a length-4 dataset with
	[xval,yval,xlabel,ylabel]
	other_ingredient_cutoff can be used to limit the amount of unspecified
	ingredients that go into a recipe"""
	data = read_data(query,cutoff)
	response = extract_rating_data(query)
	return create_model_frame(data,response,query,other_ingredient_cutoff,new_column_cutoff)

def keep_data_numbers(data):
	"""Rearranges the numeric portion of the data to be used in
	create_model_frame()"""
	data = [[x[0],x[5],x[2]/x[3]] for x in data]
	#data = numpy.asarray(data)
	return data

def create_model_frame(data,response,query,other_ingredient_cutoff = 0,new_column_cutoff=0):
	"""takes in the SQL-fetched data and then rearranges it to a 
	numpy data frame, as well as handling the response values,
	in case additional cutoffs are made"""
	ilabels = ['OTHER'] + data[1]
	ilabels = numpy.asarray(ilabels)
	rlabels = numpy.asarray(extract_recipe_labels(query))
	data = keep_data_numbers(data[0])
	k = max([x[1] for x in data])
	N = max([x[0] for x in data])
	
	new_array = numpy.zeros([N+1,k+1])
	#print "NEED TO FINISH WRITING FUNCTION"
	for x in data:
		new_array[x[0]][x[1]] += x[2]
	nremoved = 0
	#makes additional cuts if other_ingredients is too big in certain rows
	#needs way of communicating this if labels are to be saved
	#perhaps use class object
	if other_ingredient_cutoff > 0:
		cutoff1 = new_array[:,0] > other_ingredient_cutoff
		new_array = new_array[cutoff1]
		response = response[cutoff1]
		rlabels = rlabels[cutoff1]
		cutoff2 = numpy.sum(new_array>0,axis=1)>new_column_cutoff
		new_array = new_array[:,cutoff2]
		ilabels = ilabels[cutoff2]
	print str(new_array.shape[1]) + ' different ingredients'
	print str(new_array.shape[0]) + ' different recipes'
	return [new_array,response,rlabels,ilabels]

def extract_recipe_from_url(url):
	"""parses URL for recipe name;
	may need to be updated for other websites beyond allrecipes.com"""
	url = re.sub('^.*/Recipe/','',url)
	url = re.sub('/.*$','',url)
	url = re.sub('-','_',url)
	return url

#currently based on URLs
#method may need to be updated if sites other than allrecipes.com are used
def extract_recipe_labels(query):
	"""Searches for all relevant recipe URLs for a given query, and then
	it parses them to get the recipe names"""
	conn = sqlite3.connect('recipes.db')
	c = conn.cursor()
	c.execute("""CREATE TEMP TABLE qtable AS
		SELECT 
		recipe_id, url
		FROM recipes
		WHERE search_query = '%s';""" % (query))
	c.execute("""CREATE TEMP TABLE rtable AS
		SELECT url,
		recipe_id FROM qtable;""")
		
	c.execute("""UPDATE rtable SET recipe_id=
		(SELECT count(*) FROM 
		(SELECT  recipe_id AS recipe_id
		FROM rtable AS rt) rt2
		WHERE rtable.recipe_id > rt2.recipe_id
		);""")
	c.execute("""SELECT url 
		FROM rtable ORDER BY recipe_id;""")
	data = c.fetchall()
	data = [extract_recipe_from_url(x[0]) for x in data]
	c.close()
	conn.close()
	return data

#this function runs the linear programming solver
#bounds is redudnantly defined as a matrix
def solve_linear_programming(data,model):
	"""This takes in either the length-4 list of data or the first element
	of said list, as well as whatever model contains the coefficients,
	and then it constructs the constraints and solves the linear
	programming problem"""
	if type(data)==type([1,2,3]):
		print 'Taking data=data[0]'
		data = data[0]
	eqb = construct_unit_constraints(data)
	inb = construct_bounds_constraints(data)
	optim = model.coef_
	#I'm currently having issues updating scipy, so I
	#haven't tested this yet
	lp = scipy.optimize.linprog(optim,A_eq=eqb[0],b_eq = eqb[1],bounds = 
	      inb)
	return lp

#these functions are used for constructing constraints

def bounds_by_rank_kernel(x,lk,uk):
	"""This function takes in a 1D array, and 2 python lists
	with float values.  In order to create bounds, it uses these
	lists as a kernel to smooth the "bounds" of what kind of values appear
	in the data set.  Note that substitute ingredients (e.g., oil & butter)
	need to be considered separately in a function not yet created."""
	vals = numpy.sort(x)
	rvals = -numpy.sort(-x)
	lower = 0
	upper = 0
	for i,k in enumerate(lk):
		lower+=vals[i]*k
	for i,k in enumerate(uk):
		upper+=rvals[i]*k
	return [lower,upper]

def construct_bounds_constraints(x,lower_weights = [0.1,0.3,0.4,0.2],
				 upper_weights=[0.1,0.3,0.4,0.2]):
	"""This function takes in the data set and then applies
	the bounds_by_rank_kernel to each variable, returning
	a list of the [lower,upper] bounds for each variable."""
	#get bounds
	bounds = []
	for i in range(x.shape[1]):
		bounds.append(bounds_by_rank_kernel(x[:,i],lower_weights,
				      upper_weights))
	return bounds
	#K = len(bounds)
	#create matrices
	#lmatrix = -numpy.identity(K)
	#umatrix = numpy.identity(K)
	#lvals = numpy.asarray([a[0] for a in bounds])
	#uvals = numpy.asarray([a[1] for a in bounds])
	#return [numpy.row_stack((lmatrix,umatrix)),numpy.concatenate(
	#	(lvals,uvals))]
	
def require_ingredient_bounds(data,ingredient_name,bounds):
	"""This removes rows from the data that do not have an ingredient
	fall into certain bounds.  Useful in absence of actual clustering"""
	col_index = list(data[3]).index(ingredient_name)
	keep_lower = data[0][:,col_index] >= bounds[0]
	keep_upper = data[0][:,col_index] <= bounds[1]
	keep = keep_lower & keep_upper
	data[0] = data[0][keep,:]
	data[1] = data[1][keep]
	data[2] = data[2][keep]
	print "Data is now at " + str(data[0].shape[0]) + ' rows'
	return data
	

def construct_substitute_ingredient_constraints(data,maxcor = -0.5):
	pass

def construct_unit_constraints(data):
	"""Creates the constraint for all ingredients to add to 1"""
	dims = data.shape
	return [numpy.ones([1,dims[1]]),[1]]

if __name__=='__main__':
	main(sys.argv[1:])
	
	
#extra sql code down here

"""select ingredient_id,count(ingredient_id) from ingredients, 
		(select * from recipes where search_query='hummus') r 
		where ingredients.recipe_id=r.recipe_id  
		group by ingredient_id 
		order by count(*);"""