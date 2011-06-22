#chech classes for emails

import sqlconn, MySQLdb

class cDomains():
	aDomains = {}
	def __init__(self, oSqlConnect):
		if len(self.__class__.aDomains) == 0:
			self.__class__.aDomains = oSqlConnect.loaddomain()
	def check(self, sData):
		if self.__class__.aDomains.has_key(sData):
			return self.__class__.aDomains[sData]
		else:
			return "DUNNO"

class cAddr():
	aAddr = {}
	def __init__(self, oSqlConnect):
		if len(self.__class__.aAddr) == 0:
			self.__class__.aAddr = oSqlConnect.loadaddr()
	def check(self, sData):
		if self.__class__.aAddr.has_key(sData):
			return self.__class__.aAddr[sData]
		else:
			return "DUNNO"

class cUsers():
	aUsers = {}
	def __init__(self, oSqlConnect):
		if len(self.__class__.aUsers) == 0:
			self.__class__.aUsers = oSqlConnect.loaduser()
	def check(self, sRecipient, sSender):
		if self.__class__.aUsers.has_key(sRecipient):
			if self.__class__.aUsers[sRecipient].has_key(sSender):
				return self.__class__.aUsers[sRecipient][sSender]
			else:
				return "DUNNO"
		else:
			return "DUNNO"

	def ouruser(self, sData):
		return self.__class__.aUsers.has_key(sData)

	def addrule(self, sSender, sRecipient):
		self.__class__.aUsers[sSender][sRecipient] = "OK"
