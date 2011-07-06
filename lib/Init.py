# -*- coding: utf-8 -*-
#
#		System functions for policyd
#       Init.py
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
	sTmp = oConfig.get("network_type","unix")
	if sTmp == "unix":
		oSocket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
		sSockname=oConfig.get("network_socket","/var/spool/postfix/private/policy.sock")
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
	elif sTmp == "tcp":
		oSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		try:
			oSocket.bind(oConfig.get("network_address","0.0.0.0"), oConfig.get("network_port","7000"))
		except socket.error as (errno, strerror):
			print "socket.error error({0}): {1}".format(errno, strerror)
			sys.exit(1)

	oSocket.setblocking(1)
	oSocket.settimeout(None)
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

def postconf():
	PostConf = subprocess.Popen(["postconf -h smtpd_policy_service_max_ttl"], shell = True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=None)
	iDelay = int(PostConf.communicate()[0].strip()[:-1])
	return iDelay
