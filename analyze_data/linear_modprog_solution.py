#creates numpy array
import sqlite3
import scipy
import sklearn
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
	query = 'hummus'
	data = get_model_data(query)
	data = apply_response_function(data)
	xvar = data[0]
	yvar = data[1]
	#as long as no cuts are made to response value
	#an intercept would be redundant since sum(proportions)=1
	model = LassoLarsIC(criterion='aic',fit_intercept = False)
	model.fit(xvar,yvar)
	params = model.coef_
	

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
	descriptions = []
	pv = -1
	for label in labels:
		if label[0] <> pv:
			descriptions.append(label[1])
			pv = label[0]
	return descriptions

def extract_rating_data(query):
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
	data[1] = response_function(data[1])
	return data

#objective function for recipes
def response_function(y):
	return numpy.asarray([x[2]*math.log(1+x[1]) for x in y])

def get_model_data(query,cutoff=5,other_ingredient_cutoff=0,new_column_cutoff=0):
	data = read_data(query,cutoff)
	response = extract_rating_data(query)
	return create_model_frame(data,response,query,other_ingredient_cutoff,new_column_cutoff)

def keep_data_numbers(data):
	data = [[x[0],x[5],x[2]/x[3]] for x in data]
	#data = numpy.asarray(data)
	return data

def create_model_frame(data,response,query,other_ingredient_cutoff = 0,new_column_cutoff=0):
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
	url = re.sub('^.*/Recipe/','',url)
	url = re.sub('/.*$','',url)
	url = re.sub('-','_',url)
	return url

#currently based on URLs
#method may need to be updated if sites other than allrecipes.com are used
def extract_recipe_labels(query):
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

if __name__=='__main__':
	main(sys.argv[1:])
	
	
#extra sql code down here

"""select ingredient_id,count(ingredient_id) from ingredients, 
		(select * from recipes where search_query='hummus') r 
		where ingredients.recipe_id=r.recipe_id  
		group by ingredient_id 
		order by count(*);"""