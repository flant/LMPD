#Basic policy class

class Policy():
	aData = {}
	def __init__(self, aData, oSqlConn):
		self.oSqlConn = oSqlConn
		self.aData = aData

	def train(self, oData):
		return None

	def check(self, oData):
		return None
