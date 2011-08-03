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

class ReloaderTread(threading.Thread):
	def __init__(self, sleep_time, flts, debug = False):
		threading.Thread.__init__(self)
		self.debug = debug
		self.daemon = True
		self.flts = flts
		self._sleep_time = sleep_time
		if self.debug:
			self.start_time = time.time()

	def run(self):
		while (True):
			time.sleep(self._sleep_time)
			for flt in self.flts:
				try:
					flt.reload()
				except:
					if self.debug:
						print "Update problem!"
			
		if self.debug:
			stop_time = time.time()
			print "Process with name {0} started {1}, stopped {2}. Working {3} seconds.".format(self.name, time.strftime("%d.%m.%y - %H:%M:%S", time.localtime(self.start_time)), time.strftime("%d.%m.%y - %H:%M:%S", time.localtime(stop_time)), (stoptime - self.start_time))
