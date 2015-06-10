from recipe_scraper import *

class timer:
	"""this class creates a timer object
	that can be used to determine how frequently to scan something"""
	def generate_random_time(self):
		return self.floor + min(numpy.random.lognormal(self.mean,self.sd,1)[0],self.ceiling)
	def __init__(self,mean = 0.976,sd = 0.29,floor = 0.704014,ceiling = 4.307):
		self.origin = time.time()
		self.floor = floor
		self.mean = mean
		self.sd = sd
		self.ceiling = ceiling
		self.prev_time = self.origin
		self.next_counter = self.generate_random_time()
		self.nresets = 0
	def reset_time(self):
		self.prev_time = time.time()
		self.next_counter = self.generate_random_time()
	def check_time(self):
		"""this should be the only function used when
		running this normally"""
		if time.time() - self.next_counter > self.prev_time:
			self.reset_time()
			self.nresets += 1
			return True
		else:
			return False
	def get_number_resets(self):
		return self.nresets
	def get_time_remaining(self):
		return self.prev_time + self.next_counter - time.time()
	