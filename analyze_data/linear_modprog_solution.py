#creates numpy array
import sqlite3
import scipy
import sklearn
import re
import os
import sys

#todo:

#create a table of new ingredient ids to correspond to new indices, where
#0=other ingredients, 1, 2, 3, etc. refer to all other ingredients

#output this new table to python

def main(args):
	data = read_data('hummus')
	
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
		, description, idx FROM temptable;""")
	data = c.fetchall()
	c.close()
	conn.close()
	return data

def keep_data_numbers(data):
	data = [[x[0],x[5],x[2]/x[3]] for x in data]
	#data = numpy.asarray(data)
	return data

def create_model_frame(data):
	k = max([x[1] for x in data])
	N = max([x[0] for x in data])
	new_array = numpy.zeros([N,k])
	print "NEED TO FINISH WRITING FUNCTION"

def extract_ingredient_labels(data):
	pass

#database scraping needs to be updated before this function can be used
#currently recipe names are not used
def extract_recipe_labels(data):
	pass

if __name__=='__main__':
	main(sys.argv[1:])
	
	
#extra sql code down here

"""select ingredient_id,count(ingredient_id) from ingredients, 
		(select * from recipes where search_query='hummus') r 
		where ingredients.recipe_id=r.recipe_id  
		group by ingredient_id 
		order by count(*);"""