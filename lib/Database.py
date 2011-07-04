#Database connector for policyd

import MySQLdb, threading, sys, time

class ExitException(Exception):
	def __init__(self, value):
		self.value = value

	def __str__(self):
		return self.value

class Pool:
	def __init__(self, aMysql):
		self.aMysql = aMysql
		self.mutex = threading.Lock()
		self.Pool = {}
		self.Free = aMysql["pool"]
		for iNum in range(self.Free):
			self.Pool[str(iNum)] = Database(aMysql, str(iNum))

	def __enter__(self):
		iTime = aMysql["pooltime"]
		while (iTime):
			if self.Free > 0:
				for iNum in range(aMysql["pool"]):
					if self.Pool[str(iNum)].get_status():

						with mutex:
							self.Pool[str(iNum)].switch_status()
							self.Free -= self.Free

						return self.Pool[str(iNum)]
			else:
				iTime -= 1
				time.sleep(1)

		print "MySql pool is over."
		return None

	def __exit__(self, type, value, traceback):
		with self.mutex:
			self.Free += 1
			self.Pool[value].switch_status()

class Database:
	def __init__(self, aMysql, sName, iPort = 3306):
		try:
			self.aMysql = aMysql 
			self.oSqlConnect = MySQLdb.connect(self.aMysql['host'], self.aMysql['user'], self.aMysql['password'], self.aMysql['dbname'], self.aMysql['port'])
			#self.oSqlConnect.autocommit(True)
			self.bStatus = True
			self.sName = sName
		except:
				print "Can not connect to MySQL"
				sys.exit(1)
	def get_status(self):
		return self.bStatus

	def switch_status(self):
		self.bStatus = not self.bStatus
		return self.bStatus

	def set_status(self, bStatus):
		self.bStatus = bStatus
		return self.bStatus

	def execute(self, sData):
		print "Sql request: ",sData
		retry_count = self.aMysql['retry_count']
		while (retry_count):
			retry_count = retry_count - 1
			try:
				oSqlCursor = self.oSqlConnect.cursor()
				oSqlCursor.execute(sData)
				return oSqlCursor
			except MySQLdb.Error:
				self.oSqlConnect = MySQLdb.connect(self.aMysql['host'], self.aMysql['user'], self.aMysql['password'], self.aMysql['dbname'], self.aMysql['port'])

		# TODO throw exception
		return None
	
	def transaction_end(self):
		raise ExitException(self.sName)
	
