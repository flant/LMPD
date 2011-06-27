#Class for addresses

import Policy, multiprocessing

def loadsql(oSqlConn):
	sSql_1 = "SELECT `mx_addr`, `accept` FROM `white_list_addr`"
	aRes = {}
	oData = oSqlConn.execute(sSql_1)
	for row in oData:
		aRes[row[0]] = row[1]
	return aRes

def addrule(oData, oSqlConn):
	sSql_1 = "INSERT INTO `white_list_addr` VALUES(NULL, {0}, {1})"

	oSqlConn.execute(sSql_1.format(oData["address"], oData["answer"]))

class AddressPolicy(Policy.Policy):
	def __init__(self, aData, oSqlConn):
		self.mutex = multiprocessing.Lock()
		Policy.Policy.__init__(self, aData, oSqlConn)

	def check(self, oData):
		sAddr = oData["client_address"]
		if self.aData.has_key(sAddr):
			return self.aData[sAddr]
		else:
			return None
