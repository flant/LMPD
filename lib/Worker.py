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
	def __init__(self, Conn, Filters, DefaultAnswer, SqlPool, Debug = False):
		threading.Thread.__init__(self)
		self.Debug = Debug
		self.daemon = True
		self.DefaultAnswer = DefaultAnswer
		self.Socket = Conn
		self.SqlPool = SqlPool
		self.Filters = Filters
		if self.Debug:
			self.starttime = time.time()

	def run(self):
		with Connection.Connection(self.Socket, self.name, self.Debug) as conn:
			while conn.get_message():

				Answer = self.DefaultAnswer

				if conn["sender"] != "" and conn["recipient"] != "":
					if self.Debug:
						print "Mail from {0} to {1} with SASL: {2}".format(conn["sender"], conn["recipient"], conn["sasl_username"])
					for Filter in self.Filters:
						Tmp = Filter.check(conn)
						if Tmp:
							break

					if Tmp:
						Answer = Tmp

					if self.Debug:
						print "Answer was: {0}".format(Answer)

				if conn["request"] == "smtpd_access_policy":
					conn.answer(Answer)

				PySQLPool.cleanupPool()

		if self.Debug:
			stoptime = time.time()
			print "Process with name {0} started {1}, stopped {2}. Working {3} seconds.".format(self.name, time.strftime("%d.%m.%y - %H:%M:%S", time.localtime(self.starttime)), time.strftime("%d.%m.%y - %H:%M:%S", time.localtime(stoptime)), (stoptime - self.starttime))		

		sys.exit(0)
