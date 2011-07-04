#Class for addresses

import Policy, threading, Database

def loadsql(oSqlPool):
	sSql_1 = "SELECT `mx_addr`, `accept` FROM `white_list_addr`"
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
