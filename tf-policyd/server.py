#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#		Main process(connection manager) for policyd
#       server.py
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

import os, sys, signal, site

def main():
	site.addsitedir("./lib", known_paths=None)
	site.addsitedir("./plugins", known_paths=None)
	site.addsitedir("./lib/PySQLPool", known_paths=None)
	import Analyse, Config, Init, Connection, Policy, Worker, Logger, PySQLPool
	Config = Config.Config()

	signal.signal(signal.SIGTERM, lambda x, y: Init.fSIGINThandler(Config.get("argv_pid", "/tmp/policyd.pid"), x, y))
	signal.signal(signal.SIGINT, lambda x, y: Init.fSIGINThandler(Config.get("argv_pid", "/tmp/policyd.pid"), x, y))
	signal.signal(signal.SIGHUP, signal.SIG_IGN)

	Init.baseinit(Config)
	Socket = Init.createsock(Config)
	
	Mysql = Config.get("mysql", False)
	if Mysql:
		PySQLPool.getNewPool().maxActiveConnections = Config.get("mysql_pool", 10)
		Pool = PySQLPool.getNewConnection(username=Config.get("mysql_user", "root"), password=Config.get("mysql_password", ""), host=Config.get("mysql_host", "localhost"), db=Config.get("mysql_dbname", "postfix"), port=Config.get("mysql_port", 3306))
	else:
		print "Lost fields in mysql config. Exiting..."
		sys.exit(1)

	ImportFilters = Config.get("filters_order", False)
	if ImportFilters:
		ImportFilters = ["AddressPolicy","DomainPolicy","UserPolicy"]

	Filters = []
	for Filter in ImportFilters:
		globals()[Filter] = locals()[Filter] = __import__(Filter, globals(), locals(), [], -1)
		Tmp = getattr(locals()[Filter], Filter)(locals()[Filter].loadsql(Pool), Pool)
		Filters.append(Tmp)

	DefaultAnswer = Config.get("filters_default", False)
	if not DefaultAnswer:
		print "Lost fields in filter config. Exiting..."
		sys.exit(1)

	Init.demonize(Config)

	while 1:
		Conn, Addr = Socket.accept()
		Proc = Worker.WorkerTread(Conn, Filters, DefaultAnswer, Pool)
		try:
			Proc.start()
		except(thread.error):
			print("Spawned threads : %s. Can not spawn other one" % threading.active_count())


if __name__ == "__main__":
	main()

