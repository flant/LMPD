#Unix specific functions for daemons

import os, sys, argparse, grp, pwd, yaml, socket

class cConfig(dict):
	oArgs = 0
	def __init__(self):
		dict.__init__(self)
		oParser = argparse.ArgumentParser(description='Mini whitelisting daemon.')
		oParser.add_argument('-c', '--config', help='Path to a config file', default='/etc/postfix/policyd.conf')
		oParser.add_argument('-p', '--pid', help='Path to a PID file', default='/var/run/policyd.pid')
		oParser.add_argument('-d', dest='bDaemon', action='store_true', help='Become a daemon', default=False)
		self.__class__.oArgs = oParser.parse_args()
		
		if os.path.exists(self.__class__.oArgs.config):
			oConfFile = open(self.__class__.oArgs.config)
			oTmp = yaml.load(oConfFile)
			for key in oTmp:
				self[key] = oTmp[key]
			oConfFile.close
		else:
			print "Cound not find config file. Exiting..."
			sys.exit(1)

	def applyconfig(self):
		if os.path.exists(self.__class__.oArgs.pid):
			print "Another policyd works. Exiting..."
			sys.exit(1)

		if os.getuid() == 0:
			try:
				os.setuid(pwd.getpwnam(self["duser"])[2])
			except KeyError:
				print "Using existing user"
			except OSErroras as (errno, strerror):
				print "OSError error({0}): {1}".format(errno, strerror)
				sys.exit(1)

		if os.getgid() == 0:
			try:
				os.setgid(grp.getgrnam(self["dgroup"])[2])
			except KeyError:
				print "Using existing group"
			except OSErroras as (errno, strerror):
				print "OSError error({0}): {1}".format(errno, strerror)
				sys.exit(1)

	def createsock(self):
		if self.has_key("socket"):
			sSockname = self["socket"]
		else:
			sSockname="/var/spool/postfix/private/policy.sock"
			self["socket"] = sSockname

		oSocket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

		if os.path.exists(sSockname):
			try:
				os.remove(sSockname)
			except OSError as (errno, strerror):
				print "OSError error({0}): {1}".format(errno, strerror)
				sys.exit(1)

		try:
			oSocket.bind(sSockname)
		except socket.error as (errno, strerror):
			print "socket.error error({0}): {1}".format(errno, strerror)
			sys.exit(1)

		oSocket.listen(1)
		return oSocket

	def demonize(self):
		if self.__class__.oArgs.bDaemon == True:
			try: 
				iPid = os.fork()
				if iPid > 0:
					print "Daemon PID %d" % iPid
					sys.exit(0) 
			except OSError as (errno, strerror):
				print "OSError error({0}): {1}".format(errno, strerror)
				sys.exit(1)

			os.chdir("/") 
			os.setsid() 
			os.umask(022)
	
			sys.stdout = open("/dev/null")
			sys.stderr = open("/dev/null","w")
			sys.stdin = open("/dev/null", "w")
		else:
			iPid = os.getpid()
		try:
			oPidFile = open(self.__class__.oArgs.pid, "w")
			oPidFile.write(str(iPid))
			oPidFile.close()
		except IOError as (errno, strerror):
			print "I/O error({0}): {1}".format(errno, strerror)
			sys.exit(1)	

def fInt_handler(iSignum, frame):
	print "Caught SIGNAL 2. Exiting..."
	
	if os.path.exists(cConfig().oArgs.pid):
		try:
			os.remove(cConfig().oArgs.pid)
		except OSError as (errno, strerror):
			print "OSError error({0}): {1}".format(errno, strerror)
			sys.exit(1)
	sys.exit(0)
