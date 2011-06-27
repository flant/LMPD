#Class for domains

import Policy, multiprocessing

def loadsql(oSqlConn):
	aRes = {}
	sSql_1 = "SELECT `id_user`,`user` FROM `users`"
	sSql_2 = "SELECT `user_id`,	`mail`,	`accept` FROM `white_list_mail`"

	aRes={}
	aUsers={}
	aRules={}

	oData = oSqlConn.execute(sSql_1)
	for row in oData:
		aUsers[str(int(row[0]))] = row[1]
		aRes[row[1]] = {}

	oData = oSqlConn.execute(sSql_2)
	for row in oData:
		aTmp = {}
		aTmp[row[1]] = row[2]
		aRes[aUsers[str(int(row[0]))]].update(aTmp)

	return aRes

def addrule(oData, oSqlConn):
	sSql_1 = "SELECT `id_user` FROM `users` WHERE `user` = %s"
	sSql_2 = "INSERT INTO `white_list_mail` VALUES(NULL, {0}, '{1}', {2})"

	oCur = oSqlConn.execute(sSql_1, oData["sender"])
	sTmp = str(int(oCur.fetchone()[0]))

	oSqlConn.execute(sSql_2.format(oData["sender"], oData["recipient"]))

class UserPolicy(Policy.Policy):
	mutex = multiprocessing.Lock()
	def __init__(self, aData, oSqlConn):
		Policy.Policy.__init__(self, aData, oSqlConn)

	def check(self, oData):
		sRecipient = oData["recipient"]
		sSender = oData["sender"]
		if self.aData.has_key(sRecipient):
			if self.aData[sRecipient].has_key(sSender):
				return self.aData[sRecipient][sSender]
			else:
				return None

	def train(self, oData):
		with mutex:
			addrule(sSender, sRecipient)
			self.aData[sSender][sRecipient] = "OK"

		return None
