#Basic policy class

class Policy():
	aData = {}
	def __init__(self, aData, oSqlPool):
		self.oSqlPool = oSqlPool
		self.aData = aData

	def train(self, oData):
		return None

	def check(self, oData):
		return None
