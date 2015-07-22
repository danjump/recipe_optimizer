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
	
def read_data(query):
	"""reads in the data from the sql database
	technically not safe from injections because of 
	the query, but as long as you don't do anything like
	query = 'DROP TABLE ingredients;DROP TABLE recipes;',
	we should be fine
	"""
	os.chdir('/home/max/workspace/recipe_optimizer')
	conn = sqlite3.connect('recipes.db')
	c = conn.cursor()
	c.execute("""CREATE TEMP TABLE temptable AS SELECT 
		fr.recipe_id,ingredient_id, amount,
		yield_quantity,description,-1 AS idx
		FROM (SELECT 
		CASE
		WHEN summary.total < 5 THEN 0
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
		recipe_id,sum(amount) AS yield_quantity FROM ingredients
		GROUP BY recipe_id) sr
		ON fr.recipe_id = sr.recipe_id;""" % (query))
	c.execute("""UPDATE temptable SET idx=
		(SELECT count(*) FROM 
		(SELECT DISTINCT ingredient_id AS ingredient_id
		FROM temptable AS tt) tt2
		WHERE temptable.ingredient_id > tt2.ingredient_id
		);""")
	c.execute("""SELECT * FROM temptable;""")
	data = c.fetchall()
	c.close()
	conn.close()

if __name__=='__main__':
	main(sys.argv[1:])
	
	
#extra sql code down here

"""select ingredient_id,count(ingredient_id) from ingredients, 
		(select * from recipes where search_query='hummus') r 
		where ingredients.recipe_id=r.recipe_id  
		group by ingredient_id 
		order by count(*);"""