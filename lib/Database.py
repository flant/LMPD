#Database connector for policyd

import MySQLdb, multiprocessing, sys

class Database:
	def __init__(self, aMysql, iPort = 3306):
		self.mutex = multiprocessing.Lock()
		try:
			self.aMysql = aMysql 
			self.oSqlConnect = MySQLdb.connect(self.aMysql['host'], self.aMysql['user'], self.aMysql['password'], self.aMysql['dbname'], self.aMysql['port'])
		except:
				print "Can not connect to MySQL"
				sys.exit(1)

		self.oSqlCursor = self.oSqlConnect.cursor()

	def execute(self, sData):
		with self.mutex:
			retry_count = self.aMysql['retry_count']
			while (retry_count):
				retry_count = retry_count - 1
				try:
					self.oSqlCursor.execute(sData)
					break
				except MySQLdb.Error:
					self.oSqlConnect = MySQLdb.connect(self.aMysql['host'], self.aMysql['user'], self.aMysql['password'], self.aMysql['dbname'], self.aMysql['port'])
					self.oSqlCursor = self.oSqlConnect.cursor()
					self.oSqlCursor.execute(sData)

		return self.oSqlCursor
