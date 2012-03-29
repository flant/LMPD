# -*- coding: utf-8 -*-
#
#       Worker class for lmpd
#       Worker.py
#       
#       Copyright (C) 2009-2011 CJSC Flant (www.flant.ru)
#       Written by Nikolay "GyRT" Bogdanov <nikolay.bogdanov@flant.ru>
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

import threading, sys, Connection, PySQLPool, time, signal, Init, traceback, logging

class WorkerTread(threading.Thread):
	def __init__(self, socket, flts, default_answer, sql_pool, debug = False):
		threading.Thread.__init__(self)
		self.debug = debug
		self.daemon = True
		self.default_answer = default_answer
		self.socket = socket
		self.sql_pool = sql_pool
		self.flts = flts
		self._mutex = threading.Lock()

		if self.debug:
			self.start_time = time.time()

	def run(self):
		
		with Connection.Connection(self.socket, self.name, self.debug) as conn:
			while conn.get_message():

				answer = self.default_answer

				if conn["sender"] != "" and conn["recipient"] != "":
					if self.debug:
						logging.debug("Mail from {0} to {1} with SASL: {2}".format(conn["sender"], conn["recipient"], conn["sasl_username"]))
					for flt in self.flts:
						with self._mutex:
							try:
								flt_answer = flt.check(conn)
							except:
								logging.error('Error, while check address! Traceback: \n{0}\n'.format(traceback.format_exc()))
						if flt_answer:
							break

					if flt_answer:
						answer = flt_answer

					if self.debug:
						logging.debug("Answer for mail {0} to {1} was: {2}".format(conn["sender"], conn["recipient"], answer))

				if conn["request"] == "smtpd_access_policy":
					conn.answer(answer)
				try:
					PySQLPool.cleanupPool()
				except:
					logging.warn('Error, while cleanging pool! Traceback: \n{0}\n'.format(traceback.format_exc()))
		if self.debug:
			stop_time = time.time()
			logging.debug("Process with name {0} started {1}, stopped {2}. Working {3} seconds.".format(self.name, time.strftime("%d.%m.%y - %H:%M:%S", time.localtime(self.start_time)), time.strftime("%d.%m.%y - %H:%M:%S", time.localtime(stop_time)), (stop_time - self.start_time)))
