#Class for domains

import Policy, multiprocessing

def loadsql(oSqlConn):
	sSql_1 = "SELECT `dns`, `accept` FROM `white_list_dns`"
	aRes = {}
	oData = oSqlConn.execute(sSql_1)
	for row in oData:
		aRes[row[0]] = row[1]
	return aRes

def addrule(oData, oSqlConn):
	sSql_1 = "INSERT INTO `white_list_dns` VALUES(NULL, {0}, {1})"

	oSqlConn.execute(sSql_1.format(oData["helo_name"], oData["answer"]))

class DomainPolicy(Policy.Policy):
	mutex = multiprocessing.Lock()
	def __init__(self, aData, oSqlConn):
		Policy.Policy.__init__(self, aData, oSqlConn)

	def check(self, oData):
		sDomain = oData["helo_name"]
		if self.aData.has_key(sDomain):
			return self.aData[sDomain]
		else:
			return None
