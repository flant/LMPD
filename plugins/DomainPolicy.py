#Class for domains

import Policy, threading, PySQLPool

def loadsql(oSqlPool):
	sSql_1 = "SELECT `dns`, `accept` FROM `white_list_dns`"
	aRes = {}

	query = PySQLPool.getNewQuery(oSqlPool, True)
	query.Query(sSql_1)
			
	for row in query.record:
		aRes[row[0]] = row[1].lower()
			
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
