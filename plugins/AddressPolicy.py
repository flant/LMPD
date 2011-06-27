#Class for addresses

import Policy, multiprocessing

def loadsql(oSqlConn):
	sSql_1 = "SELECT `mx_addr`, `accept` FROM `white_list_addr`"
	aRes = {}
	oSqlConn.execute(sSql_1)
	for row in oSqlConn:
		aRes[row[0]] = row[1]
	return aRes

def addrule(oData, oSqlConn):
	sSql_1 = "INSERT INTO `white_list_addr` VALUES(NULL, {0}, 'OK')"

	oSqlConn.execute(sSql_1.format(oData["client_address"]))

class AddressPolicy(Policy.Policy):
	mutex = multiprocessing.Lock()
	def __init__(self, aData, oSqlConn):
		Policy.Policy.__init__(self, aData, oSqlConn)

	def check(self, oData):
		sAddr = oData["client_address"]
		if self.aData.has_key(sAddr):
			return self.aData[sAddr]
		else:
			return None
