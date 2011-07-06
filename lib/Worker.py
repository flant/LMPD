#Worker class for policyd

import threading, sys, Connection, PySQLPool, Init

class WorkerTread(threading.Thread):
	def __init__(self, oConn, aFilters, sDefaultAnswer, oSqlPool):
		threading.Thread.__init__(self)
		self.daemon = True
		self.sDefaultAnswer = sDefaultAnswer
		self.oSocket = oConn
		self.oSqlPool = oSqlPool
		self.aFilters = aFilters

	def run(self):
		with Connection.Connection(self.oSocket) as conn:
			while conn.get_message():
				sTmp = conn["request"]
				#print conn
				if sTmp == "smtpd_access_policy":
					if conn["sender"] != "" and conn["recipient"] != "":
						#print conn
						if conn["sasl_username"] != "":
							print "Mail from {0} to {1} with SASL: {2}".format(conn["sender"], conn["recipient"], conn["sasl_username"])
						for oFilter in self.aFilters:
							sTmp = oFilter.check(conn)
							if sTmp: break

						if sTmp:
							sAnswer = sTmp
						else:
							sAnswer = self.sDefaultAnswer
						#print sAnswer
					else:
						sAnswer = self.sDefaultAnswer
					conn.answer(sAnswer)

				elif sTmp == "junk_policy":
					pass
				else:
					pass

				PySQLPool.cleanupPool()
			
