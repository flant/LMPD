#Worker class for policyd

import multiprocessing, sys, Connection

class WorkerTread(multiprocessing.Process):
	def __init__(self, oConn, aFilters, sDefaultAnswer, oSqlConn):
		multiprocessing.Process.__init__(self)
		self.daemon = True
		self.sDefaultAnswer = sDefaultAnswer
		self.oSocket = oConn
		self.oSqlConn = oSqlConn
		self.aFilters = aFilters

	def run(self):
		with Connection.Connection(self.oSocket) as conn:
			while conn.get_message():
				sTmp = conn["request"]

				if sTmp == "smtpd_access_policy":

					for oFilter in self.aFilters:
						sTmp = oFilter.check(conn)
						if sTmp: break

					if sTmp:
						sAnswer = sTmp
					else:
						sAnswer = self.sDefaultAnswer

					conn.answer(sAnswer)

				elif sTmp == "junk_policy":
					pass
				else:
					pass

		#self.oConnection.close()
		#sys.exit(0)
