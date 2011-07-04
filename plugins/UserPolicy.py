#Class for domains

import Policy, threading

def loadsql(oSqlPool):
	aRes = {}
	sSql_1 = "SELECT `id`,`address` FROM `white_list_users`"
	sSql_2 = "SELECT `user_id`, `mail`, `accept` FROM `white_list_mail`"

	aRes={}
	aUsers={}
	aRules={}
	try:
		with oSqlPool as oSqlConn:
			oData = oSqlConn.execute(sSql_1)
			for row in oData:
				sTmp = row[1].lower()
				aUsers[str(int(row[0]))] = sTmp
				aRes[sTmp] = {}

			oData = oSqlConn.execute(sSql_2)
			for row in oData:
				aTmp = {}
				aTmp[row[1].lower()] = row[2]
				aRes[aUsers[str(int(row[0]))]].update(aTmp)
				oSqlConn.transaction_end()
	except ExitException as e:
		pass
	return aRes

def addrule(oData, oSqlPool, sAnswer = "OK"):
	if oData["sender"] != "" and oData["recipient"] != "":
		print "Start train sqlfunc"
		sSql_1 = "SELECT `id` FROM `white_list_users` WHERE `address` LIKE '{0}'"
		sSql_2 = "INSERT IGNORE INTO `white_list_mail` VALUES(NULL, {0}, '{1}', '{2}')"

		try:
			with oSqlPool as oSqlConn:
				oData = oSqlConn.execute(sSql_1.format(oData["sender"]))
				sTmp = str(int(oData.fetchone()[0]))
				#print "sTmp in sql func: ", sTmp
				oSqlConn.execute(sSql_2.format(sTmp, oData["recipient"], sAnswer))
				oSqlConn.transaction_end()
		except ExitException as e:
			pass

class UserPolicy(Policy.Policy):
	def __init__(self, aData, oSqlPool):
		self.mutex = threading.Lock()
		Policy.Policy.__init__(self, aData, oSqlPool)

	def check(self, oData):
		#if oData["recipient"] == "gyrt@list.ru": print oData
			
		if oData["sasl_username"] == "":
			sRecipient = oData["recipient"]
			sSender = oData["sender"]
			
			if self.aData.has_key(sRecipient):
				if self.aData[sRecipient].has_key(sSender):
					return self.aData[sRecipient][sSender]
				else:
					return None
		else:
			self.train(oData)
			return None

	def train(self, oData, sAnswer = "OK"):
		with self.mutex:
			sRecipient = oData["recipient"]
			sSender = oData["sender"]
			if sRecipient != "" and sSender != "":
				#print "Start training"
				#print oData
				addrule(oData, self.oSqlPool, sAnswer)
				if not self.aData.has_key(sSender): self.aData[sSender] = {}
				if not self.aData[sSender].has_key(sRecipient):
					self.aData[sSender][sRecipient] = sAnswer
					print self.aData[sSender][sRecipient]
		return None
