#
# Copyright (C) 2009-2011 CJSC TrueOffice (www.trueoffice.ru)
# Written by Dmitry Stolyarov <dmitry.stolyarov@trueoffice.ru>
#

# -*- coding: utf-8 -*-

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
