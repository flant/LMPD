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
	oConfig = Config.Config()

	signal.signal(signal.SIGTERM, lambda x, y: Init.fSIGINThandler(oConfig.get("argv_pid", "/tmp/policyd.pid"), x, y))
	signal.signal(signal.SIGINT, lambda x, y: Init.fSIGINThandler(oConfig.get("argv_pid", "/tmp/policyd.pid"), x, y))
	signal.signal(signal.SIGHUP, signal.SIG_IGN)

	Init.baseinit(oConfig)
	oSocket = Init.createsock(oConfig)
	
	aMysql = oConfig.get("mysql", False)
	if aMysql:
		PySQLPool.getNewPool().maxActiveConnections = oConfig.get("mysql_pool", 10)
		oPool = PySQLPool.getNewConnection(username=oConfig.get("mysql_user", "root"), password=oConfig.get("mysql_password", ""), host=oConfig.get("mysql_host", "localhost"), db=oConfig.get("mysql_dbname", "postfix"), port=oConfig.get("mysql_port", 3306))
	else:
		print "Lost fields in mysql config. Exiting..."
		sys.exit(1)

	aImportFilters = oConfig.get("filters_order", False)
	if aImportFilters:
		aImportFilters = ["AddressPolicy","DomainPolicy","UserPolicy"]

	aFilters = []
	for sFilter in aImportFilters:
		globals()[sFilter] = locals()[sFilter] = __import__(sFilter, globals(), locals(), [], -1)
		oTmp = getattr(locals()[sFilter], sFilter)(locals()[sFilter].loadsql(oPool), oPool)
		aFilters.append(oTmp)

	sDefaultAnswer = oConfig.get("filters_default", False)
	if not sDefaultAnswer:
		print "Lost fields in filter config. Exiting..."
		sys.exit(1)

	Init.demonize(oConfig)

	while 1:
		oConn, oAddr = oSocket.accept()
		tProc = Worker.WorkerTread(oConn, aFilters, sDefaultAnswer, oPool, True)
		try:
			tProc.start()
		except(thread.error):
			print("Spawned threads : %s. Can not spawn other one" % threading.active_count())


if __name__ == "__main__":
	main()

