#Class for addresses

import Policy, threading, PySQLPool

def loadsql(oSqlPool):
	sSql_1 = "SELECT `mx_addr`, `accept` FROM `white_list_addr`"
	aRes = {}

	query = PySQLPool.getNewQuery(oSqlPool, True)
	query.Query(sSql_1)		

	for row in query.record:
		aRes[row[0]] = row[1].lower()

	return aRes
#Dont need now
#def addrule(oData, oSqlPool):
#	sSql_1 = "INSERT INTO `white_list_addr` VALUES(NULL, {0}, {1})"
#
#	oSqlConn.execute(sSql_1.format(oData["address"], oData["answer"]))

class AddressPolicy(Policy.Policy):
	def __init__(self, aData, oSqlPool):
		self.mutex = threading.Lock()
		Policy.Policy.__init__(self, aData, oSqlPool)

	def check(self, oData):
		sAddr = oData["client_address"]
		if self.aData.has_key(sAddr):
			return self.aData[sAddr]
		else:
			return None
