#!/usr/bin/env python

#Server.py for postfix policy daemon

import os, sys, signal, site

def main():
	site.addsitedir("./lib", known_paths=None)
	site.addsitedir("./plugins", known_paths=None)
	import Analyse, Config, Init, Database, Connection, Policy, Worker
	oConfig = Config.Config()

	signal.signal(signal.SIGTERM, lambda x, y: Init.fSIGINThandler(oConfig.get("argv_pid", "/tmp/policyd.pid"), x, y))
	signal.signal(signal.SIGINT, lambda x, y: Init.fSIGINThandler(oConfig.get("argv_pid", "/tmp/policyd.pid"), x, y))
	signal.signal(signal.SIGHUP, signal.SIG_IGN)

	Init.baseinit(oConfig)
	oSocket = Init.createsock(oConfig)
	
	aMysql = oConfig.get("mysql", False)
	if aMysql:
		oDatabase = Database.Database(aMysql)
	else:
		print "Lost fields in mysql config. Exiting..."
		sys.exit(1)

	aImportFilters = oConfig.get("filters_order", False)
	if aImportFilters:
		aImportFilters = ["AddressPolicy","DomainPolicy","UserPolicy"]

	aFilters = []
	for sFilter in aImportFilters: #TODO automatic filter load from config
		globals()[sFilter] = locals()[sFilter] = __import__(sFilter, globals(), locals(), [], -1)
		oTmp = getattr(locals()[sFilter], sFilter)(locals()[sFilter].loadsql(oDatabase), oDatabase)
		aFilters.append(oTmp)

	sDefaultAnswer = oConfig.get("filters_default", False)
	if not sDefaultAnswer:
		print "Lost fields in filter config. Exiting..."
		sys.exit(1)

	Init.demonize(oConfig)

	while 1:
		oConn, oAddr = oSocket.accept()
		tProc = Worker.WorkerTread(oConn, aFilters, sDefaultAnswer, oDatabase)
		tProc.start()

if __name__ == "__main__":
	main()

