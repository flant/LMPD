# -*- coding: utf-8 -*-
#
#       Logger for loging
#       Logger.py
#       
#       Copyright (C) 2009-2011 CJSC Flant (www.flant.ru)
#       Written by Dmitry Stolyarov <dmitry.stolyarov@flant.ru>
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

import datetime

import syslog

class Logger:
	DEBUG = 0
	INFO = 1
	NOTICE = 2
	WARNING = 3
	ERR = 4

	def log(self, *args):
		if len(args) == 1:
			priority = self.INFO
			message = args[0]
		else:
			priority = args[0]
			message = "".join(args[1:])

		print "{0}: {1}: {2}".format(
			datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
			self._get_priority_name(priority),
			message
		)

	def _get_priority_name(self, priority):
		return ['DEBUG', 'INFO', 'NOTICE', 'WARNING', 'ERR'][priority]

class LoggerSyslog(Logger):
	def __init__(self, name):
		syslog.openlog(name, syslog.LOG_PID, syslog.LOG_DAEMON)

	def log(self, *args):
		if len(args) == 1:
			priority = self.INFO
			message = args[0]
		else:
			priority = args[0]
			message = "".join(args[1:])

		syslog.syslog(self._get_syslog_priority(priority), message)

	def _get_syslog_priority(self, priority):
		return [syslog.LOG_DEBUG, syslog.LOG_INFO, syslog.LOG_NOTICE, syslog.LOG_WARNING, syslog.LOG_ERR][priority]
