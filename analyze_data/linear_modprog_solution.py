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
	os.chdir('/home/max/workspace/recipe_optimizer')
	conn = sqlite3.connect('recipes.db')
	c = conn.cursor()
	c.execute('CREATE TABLE temp_table
		(ingredient_id INTEGER,
		recipe_id INTEGER,
		proportion REAL);')
	c.execute("""SELECT fr.recipe_id,ingredient_id, amount,yield_quantity,description FROM (SELECT 
		CASE
		WHEN summary.total < 5 THEN 0
		ELSE ingredients.ingredient_id
		END AS ingredient_id,
		recipe_id, description,amount
		FROM ingredients,
		(SELECT ingredient_id,count(ingredient_id) AS total FROM ingredients, 
		(SELECT * FROM recipes WHERE search_query='hummus') r 
		WHERE ingredients.recipe_id=r.recipe_id  
		GROUP BY ingredient_id 
		ORDER BY count(*)) summary
		WHERE summary.ingredient_id = ingredients.ingredient_id) fr
		INNER JOIN (SELECT recipe_id, yield_quantity FROM recipes) sr
		ON fr.recipe_id = sr.recipe_id;""")


if __name__=='__main__':
	main(sys.argv[1:])
	
	
#extra sql code down here

"""select ingredient_id,count(ingredient_id) from ingredients, 
		(select * from recipes where search_query='hummus') r 
		where ingredients.recipe_id=r.recipe_id  
		group by ingredient_id 
		order by count(*);"""