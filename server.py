#!/usr/bin/env python

#Server.py for postfix policy daemon

import socket, os, time, sys, threading, argparse, signal, yaml, MySQLdb, grp, pwd, proto, regex, sysspecif, sqlconn, check

class cWorkerTread(threading.Thread):
	def __init__(self,oSocket, oSqlConn):
		threading.Thread.__init__(self)
		self.daemon = True
		self.oProtocol = oSocket
		self.oSqlConn = oSqlConn
	def run(self):
		sData = regex.cParser(self.oProtocol.getdata())
		#TODO whitelist check
		sResult = "DUNNO"
		if check.cUsers(self.oSqlConn).ouruser(sData["sender"]) == False:
			sTmp = check.cDomains(self.oSqlConn).check(sData["client_name"])                
			if sTmp == "DUNNO":
				sTmp = check.cAddr(self.oSqlConn).check(sData["client_address"])
				if sTmp == "DUNNO":
					sTmp = check.cUsers(self.oSqlConn).check(sData["recipient"], sData["sender"])
					if sTmp == "DUNNO":
						sResult = sTmp
					else:
						sResult = sTmp
				else:
					sResult = sTmp
			else:
				sResult = sTmp
		else:
			if check.cUsers(self.oSqlConn).check(sData["sender"], sData["recipient"]) == "DUNNO":
				check.cUsers(self.oSqlConn).addrule(sData["sender"], sData["recipient"])
				sResult = "DUNNO"

		self.oProtocol.answer(sResult)
		del self.oProtocol
		sys.exit(0)

def main():

	signal.signal(signal.SIGINT, sysspecif.fInt_handler)
	
	oConfig = sysspecif.cConfig()
	oConfig.applyconfig()
	oSocket = oConfig.createsock()

	oSqlConn = sqlconn.cSqlConnection(oConfig["host"], oConfig["user"], oConfig["password"], oConfig["dbname"], oConfig["port"])
	oDomains = check.cDomains(oSqlConn)
	oUsers = check.cUsers(oSqlConn)
	oAddr = check.cAddr(oSqlConn)

	oConfig.demonize()

	while 1:
		oConn, oAddr = oSocket.accept()
		tProc = cWorkerTread(proto.cPRProtocol(oConn), oSqlConn)
		tProc.start()

if __name__ == "__main__":
	main()
