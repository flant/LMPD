#Class for domains

import Policy, threading, Database

def loadsql(oSqlPool):
	sSql_1 = "SELECT `dns`, `accept` FROM `white_list_dns`"
	aRes = {}
	try:
		with oSqlPool as oSqlConn:
			oData = oSqlConn.execute(sSql_1)
			
			for row in oData:
				aRes[row[0]] = row[1].lower()
			
			oSqlConn.transaction_end()
	except Database.ExitException as e:
		pass
	return aRes
#Dont need now
#def addrule(oData, oSqlConn):
#	sSql_1 = "INSERT INTO `white_list_dns` VALUES(NULL, {0}, {1})"
#
#	oSqlConn.execute(sSql_1.format(oData["helo_name"], oData["answer"]))

class DomainPolicy(Policy.Policy):
	def __init__(self, aData, oSqlPool):
		self.mutex = threading.Lock()
		Policy.Policy.__init__(self, aData, oSqlPool)

	def check(self, oData):
		sDomain = oData["helo_name"]
		if self.aData.has_key(sDomain):
			return self.aData[sDomain]
		else:
			return None
