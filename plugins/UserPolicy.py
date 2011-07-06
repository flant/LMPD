#Class for domains

import Policy, threading, PySQLPool, subprocess

def loadsql(oSqlPool):
	aRes = {}
	sSql_1 = "SELECT `id`,`address` FROM `white_list_users`"
	sSql_2 = "SELECT `user_id`, `mail`, `accept` FROM `white_list_mail`"

	aRes={}
	aUsers={}
	aRules={}
	query = PySQLPool.getNewQuery(oSqlPool, True)
	query.Query(sSql_1)
	for row in query.record:
		sTmp = row["address"].lower()
		aUsers[str(int(row["id"]))] = sTmp
		aRes[sTmp] = {}

	query.Query(sSql_2)
	for row in query.record:
		aTmp = {}
		aTmp[row["mail"].lower()] = row["accept"]
		aRes[aUsers[str(int(row["user_id"]))]].update(aTmp)

	return aRes

def addrule(oData, oSqlPool, sAnswer = "OK"):
	if oData["sender"] != "" and oData["recipient"] != "":
		#print "Start train sqlfunc"
		sSql_1 = "SELECT `id` FROM `white_list_users` WHERE `address` LIKE '{0}'"
		sSql_2 = "INSERT IGNORE INTO `white_list_mail` VALUES(NULL, {0}, '{1}', '{2}')"

		query = PySQLPool.getNewQuery(oSqlPool, True)
		query.Query(sSql_1.format(oData["sender"]))
		sTmp = str(int(query.record.fetchone()[0]))
		#print "sTmp in sql func: ", sTmp
		query.Query(sSql_2.format(sTmp, oData["recipient"], sAnswer))

class UserPolicy(Policy.Policy):
	def __init__(self, aData, oSqlPool):
		self.mutex = threading.Lock()
		Policy.Policy.__init__(self, aData, oSqlPool)
		self.ConfAliases = self._postconf()

	def check(self, oData):
		#if oData["recipient"] == "gyrt@list.ru": print oData
			
		if oData["sasl_username"] == "":
			sSender = oData["sender"]
			aRecipient = list(set(self._postalias(oData["recipient"])))
			sAnswer = self._strict_check(oData["recipient"], sSender)
			if sAnswer:
				return sAnswer
			else:
				if aRecipient:
					for sEmail in aRecipient:
						sAnswer = self._strict_check(sEmail.lower(), sSender)
						if sAnswer: break

					if sAnswer:
						return sAnswer
					else:
						return None
				else:
					return None
		else:
			self.train(oData)
			return None

	def _strict_check(self, sRecipient, sSender):
		if self.aData.has_key(sRecipient) and self.aData[sRecipient].has_key(sSender):
			return self.aData[sRecipient][sSender]
		else:
			return None

	def _postalias(self, sRecipient):
		PostAlias = subprocess.Popen(["postalias -q {0} {1}".format(sRecipient, self.ConfAliases)], shell = True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=None)
		sOutput = PostAlias.communicate()[0].strip().lower()
	        aRes = list()
		if sOutput == sRecipient.lower().strip() or PostAlias.returncode:
			return None
		else:
			aTestMails = sOutput.split(",")
			for sEmail in aTestMails:
				aAnswer = self._postalias(sEmail.strip())
				if aAnswer:
					aRes += aAnswer
				else:
					if not sEmail in aRes:
						aRes.append(sEmail.strip())

		return aRes

	def _postconf(self):
		PostConf = subprocess.Popen(["postconf -h virtual_alias_maps alias_maps"], shell = True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=None)
		Conf = PostConf.communicate()[0].strip().replace("\n", " ").replace(",", "")
		return Conf

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
					#print self.aData[sSender][sRecipient]
		return None
