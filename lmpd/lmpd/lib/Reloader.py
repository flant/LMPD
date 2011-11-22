# -*- coding: utf-8 -*-
#
#       Base reloader class for lmpd
#       Reloader.py
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

import threading, sys, Connection, PySQLPool, Init, time, traceback, logging

class ReloaderTread(threading.Thread):
	def __init__(self, sleep_time, flts, debug = False):
		threading.Thread.__init__(self)
		self._mutex = threading.Lock()
		self.debug = debug
		self.daemon = True
		self.flts = flts
		self._sleep_time = sleep_time
		if self.debug:
			self.start_time = time.time()

	def run(self):
		while (True):
			time.sleep(self._sleep_time)
			if self.debug:
				logging.debug('Starting update process')
			for flt in self.flts:
				try:
					with self._mutex:
						flt.reload()
				except:
					logging.warn("Update problem!")
					if self.debug:
						logging.debug("Error, while updating. Traceback: \n{0}\n".format(traceback.format_exc()))
			if self.debug:
				logging.debug('Successfully update')
