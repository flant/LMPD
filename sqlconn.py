#Module for SQL connection

import MySQLdb

class cSqlConnection:
	oSqlCursor = 0
	oSqlConnect = 0
	def __init__(self, sHost, sUser, sPasswd, sDB, iPort):
		try:
			self.__class__.oSqlConnect = MySQLdb.connect(sHost, sUser, sPasswd, sDB, iPort)
		except KeyError:
			try:
				self.__class__.oSqlConnect = MySQLdb.connect(sHost, sUser, sPasswd, sDB, iPort)
			except KeyError:
				print "Can not connect to MySQL"
				sys.exit(1)
			except:
				print "Can not connect to MySQL"
				sys.exit(1)

		self.__class__.oSqlCursor = self.__class__.oSqlConnect.cursor()

	def loaddomain(self):
		sSql_1 = "SELECT `dns`, `accept` FROM `white_list_dns`"
		aRes = {}
		self.__class__.oSqlCursor.execute(sSql_1)
		for row in self.__class__.oSqlCursor:
			aRes[row[0]] = row[1]
		return aRes

	def loadaddr(self):
		sSql_1 = "SELECT `mx_addr`, `accept` FROM `white_list_addr`"
		aRes = {}
		self.__class__.oSqlCursor.execute(sSql_1)
		for row in self.__class__.oSqlCursor:
			aRes[row[0]] = row[1]
		return aRes

	def loaduser(self):
		sSql_1 = "SELECT `id_user`,`user` FROM `users`"
		sSql_2 = "SELECT `user_id`,	`mail`,	`accept` FROM `white_list_mail`"

		aRes={}
		aUsers={}
		aRules={}

		self.__class__.oSqlCursor.execute(sSql_1)
		for row in self.__class__.oSqlCursor:
			aUsers[str(int(row[0]))] = row[1]
			aRes[row[1]] = {}

		self.__class__.oSqlCursor.execute(sSql_2)
		for row in self.__class__.oSqlCursor:
			aTmp = {}
			aTmp[row[1]] = row[2]
			aRes[aUsers[str(int(row[0]))]].update(aTmp)
		return aRes

	def addrule(self, sSender, sRecipient):
		sSql_1 = "SELECT `id_user` FROM `users` WHERE `user` = %s"
		sSql_2 = "INSERT INTO `white_list_mail` VALUES(NULL, {0}, '{1}', 'OK')"
		
		self.__class__.oSqlCursor.execute(sSql_1, sSender)
		sTmp = str(int(self.__class__.oSqlCursor.fetchone()[0]))
		
		self.__class__.oSqlCursor.execute(sSql_2.format(sTmp, sRecipient))
		
