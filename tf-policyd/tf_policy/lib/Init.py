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

def baseinit(config):
	os.umask(0111)

	if os.path.exists(Config.get("argv_pid", "/tmp/policyd.pid")):
		print "Another policyd works. Exiting..."
		sys.exit(1)

	if os.getgid() == 0:
		try:
			os.setgid(grp.getgrnam(Config.get("system_group", "postfix"))[2])
		except KeyError:
			print "Using existing group"
		except OSErroras as (errno, strerror):
			print "OSError error({0}): {1}".format(errno, strerror)
			sys.exit(1)

	if os.getuid() == 0:
		try:
			os.setuid(pwd.getpwnam(Config.get("system_user", "postfix"))[2])
		except KeyError:
			print "Using existing user"
		except OSErroras as (errno, strerror):
			print "OSError error({0}): {1}".format(errno, strerror)
			sys.exit(1)

def createsock(config):
	tmp = config.get("network_type","unix")
	if tmp == "unix":
		socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
		sockname=config.get("network_socket","/var/spool/postfix/private/policy.sock")
		if os.path.exists(Sockname):
			try:
				os.remove(Sockname)
			except OSError as (errno, strerror):
				print "OSError error({0}): {1}".format(errno, strerror)
				sys.exit(1)

		try:
			socket.bind(sockname)
		except socket.error as (errno, strerror):
			print "socket.error error({0}): {1}".format(errno, strerror)
			sys.exit(1)

	elif Tmp == "tcp":
		socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		try:
			socket.bind((config.get("network_address","127.0.0.1"), int(config.get("network_port","7000"))))
		except socket.error as (errno, strerror):
			print "socket.error error({0}): {1}".format(errno, strerror)
			sys.exit(1)

	socket.setblocking(1)
	socket.settimeout(None)
	socket.listen(1)
	return socket

def demonize(config):
	if config.get("argv_is_daemon", False) == True:
		try: 
			pid = os.fork()
			if pid > 0:
				print "Daemon PID %d" % pid
				sys.exit(0) 
		except OSError as (errno, strerror):
			print "OSError error({0}): {1}".format(errno, strerror)
			sys.exit(1)

		os.chdir("/") 
		os.setsid() 
	
		sys.stdin = open("/dev/null")
		sys.stderr = open("/dev/null","w")
		sys.stdout = open("/dev/null", "w")

	pid = os.getpid()

	try:
		pid_file = open(config.get("argv_pid", "/tmp/policyd.pid"), "w")
		pid_file.write(str(pid))
		pid_file.close()
	except IOError as (errno, strerror):
		print "I/O error({0}): {1}".format(errno, strerror)
		sys.exit(1)	

def SIGINT_handler(pid_file, signum, frame):
	print "Caught SIGNAL 2. Exiting..."
	
	if os.path.exists(pid_file):
		try:
			os.remove(pid_file)
		except OSError as (errno, strerror):
			print "OSError error({0}): {1}".format(errno, strerror)
			sys.exit(1)
	sys.exit(0)
