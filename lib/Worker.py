# -*- coding: utf-8 -*-
#
#		Worker class for policyd
#       Worker.py
#       
#       Copyright (C) 2009-2011 CJSC TrueOffice (www.trueoffice.ru)
#		Written by Nikolay aka GyRT Bogdanov <nikolay.bogdanov@trueoffice.ru>
#       
#       This program is free software; you can redistribute it and/or modify
#       it under the terms of the GNU General Public License as published by
#       the Free Software Foundation; either version 2 of the License, or
#       any later version.
#       
#       This program is distributed in the hope that it will be useful,
#       but WITHOUT ANY WARRANTY; without even the implied warranty of
#       MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#       GNU General Public License for more details.
#       
#       You should have received a copy of the GNU General Public License
#       along with this program; if not, write to the Free Software
#       Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#       MA 02110-1301, USA.

import threading, sys, Connection, PySQLPool, Init, time

class WorkerTread(threading.Thread):
	def __init__(self, oConn, aFilters, sDefaultAnswer, oSqlPool):
		threading.Thread.__init__(self)
		self.daemon = True
		self.sDefaultAnswer = sDefaultAnswer
		self.oSocket = oConn
		self.oSqlPool = oSqlPool
		self.aFilters = aFilters
		self.starttime = time.strftime("%d.%m.%y - %H:%M:%S")

	def run(self):
		with Connection.Connection(self.oSocket) as conn:
			while conn.get_message():
				sTmp = conn["request"]
				#print conn
				if sTmp == "smtpd_access_policy":
					if conn["sender"] != "" and conn["recipient"] != "":
						#print conn
						#if conn["sasl_username"] != "":
						#print "Mail from {0} to {1} with SASL: {2}".format(conn["sender"], conn["recipient"], conn["sasl_username"])
						for oFilter in self.aFilters:
							sTmp = oFilter.check(conn)
							if sTmp:
								break

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

		stoptime = time.strftime("%d.%m.%y - %H:%M:%S")
		print "Process with name {0} started {1}, stopped {2}".format(self.name, self.starttime, stoptime)		
		sys.exit(0)
