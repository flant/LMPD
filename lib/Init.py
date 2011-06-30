#System special functions

import os, pwd, grp, socket, sys

def baseinit(oConfig):
	os.umask(0111)

	if os.path.exists(oConfig.get("argv_pid", "/tmp/policyd.pid")):
		print "Another policyd works. Exiting..."
		sys.exit(1)

	if os.getgid() == 0:
		try:
			os.setgid(grp.getgrnam(oConfig.get("system_group", "postfix"))[2])
		except KeyError:
			print "Using existing group"
		except OSErroras as (errno, strerror):
			print "OSError error({0}): {1}".format(errno, strerror)
			sys.exit(1)

	if os.getuid() == 0:
		try:
			os.setuid(pwd.getpwnam(oConfig.get("system_user", "postfix"))[2])
		except KeyError:
			print "Using existing user"
		except OSErroras as (errno, strerror):
			print "OSError error({0}): {1}".format(errno, strerror)
			sys.exit(1)

def createsock(oConfig):
	sSockname=oConfig.get("socket_socket","/var/spool/postfix/private/policy.sock")

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

def demonize(oConfig):
	if oConfig.get("argv_daemon", False) == True:
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
	
		sys.stdin = open("/dev/null")
		sys.stderr = open("/dev/null","w")
		sys.stdout = open("/dev/null", "w")

	iPid = os.getpid()

	try:
		oPidFile = open(oConfig.get("argv_pid", "/tmp/policyd.pid"), "w")
		oPidFile.write(str(iPid))
		oPidFile.close()
	except IOError as (errno, strerror):
		print "I/O error({0}): {1}".format(errno, strerror)
		sys.exit(1)	

def fSIGINThandler(sPidFile, iSignum, frame):
	print "Caught SIGNAL 2. Exiting..."
	
	if os.path.exists(sPidFile):
		try:
			os.remove(sPidFile)
		except OSError as (errno, strerror):
			print "OSError error({0}): {1}".format(errno, strerror)
			sys.exit(1)
	sys.exit(0)
