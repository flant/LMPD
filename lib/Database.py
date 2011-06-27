#Database connector for policyd

import MySQLdb, multiprocessing

class Database:
	mutex = multiprocessing.Lock()
	def __init__(self, aMysql, iPort = 3306):
		try:
			self.aMysql = aMysql 
			self.oSqlConnect = MySQLdb.connect(aMysql['host'], aMysql['user'], aMysql['password'], aMysql['dbname'], aMysql['port'])
		except:
				print "Can not connect to MySQL"
				sys.exit(1)

		self.oSqlCursor = self.oSqlConnect.cursor()

	def execute(self, sData):
		with mutex:
			retry_count = self.aMysql['retry_count']
			while (retry_count):
				retry_count = retry_count - 1
				try:
					oSqlCursor.execute(sData)
					break
				except:
					self.oSqlConnect = MySQLdb.connect(aMysql['host'], aMysql['user'], aMysql['password'], aMysql['dbname'], aMysql['port'])
					oSqlCursor.execute(sData)
					
