#Worker class for policyd

import multiprocessing, sys

class WorkerTread(multiprocessing.Process):
	def __init__(self,oConn, aFilters, sDefaultAnswer, oSqlConn):
		multiprocessing.Process.__init__(self)
		self.daemon = True
		self.sDefaultAnswer = sDefaultAnswer
		self.oConnection = oConn
		self.oSqlConn = oSqlConn
		self.aFilters = aFilters

	def run(self):
		sTmp = self.oConnection["request"]

		if sTmp == "smtpd_access_policy":

			for oFilter in self.aFilters:
				sTmp = oFilter.check(self.oConnection)
				if sTmp:
					break

			if sTmp:
				sAnswer = sTmp
			else:
				sAnswer = self.sDefaultAnswer

			self.oConnection.answer(sAnswer)
		elif sTmp == "junk_policy":
			pass
		else:
			pass

		self.oConnection.close()
		sys.exit(0)
