# -*- coding: utf-8 -*-
#
#       System functions for LMPD (http://flant.ru/projects/lmpd)
#       Init.py
#       
#       Copyright (C) 2009-2012 CJSC Flant (www.flant.ru)
#       Written by Nikolay "GyRT" Bogdanov <nikolay.bogdanov@flant.ru>
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

import os, pwd, grp, socket, sys, PySQLPool, logging, traceback

def check_clone(pid_file):
	if os.path.exists(pid_file):
		logging.error("Another LMPD process is in work. Exiting...")
		sys.exit(1)

def limits():
	return 100

def baseinit(config):
	os.umask(0111)

	if os.getgid() == 0:
		try:
			os.setgid(grp.getgrnam(config.get("system_group", "postfix"))[2])
		except KeyError:
			logging.warn("Using existing group")
		except:
			logging.error("Error in getting GID. Traceback: \n{0}\n".format(traceback.format_exc()))
			sys.exit(1)

	if os.getuid() == 0:
		try:
			os.setuid(pwd.getpwnam(config.get("system_user", "postfix"))[2])
		except KeyError:
			logging.warn("Using existing user")
		except OSErroras as (errno, strerror):
			logging.error("Error in getting UID. Traceback: \n{0}\n".format(traceback.format_exc()))
			sys.exit(1)

def createsock(config):
	net_type = config.get("network_type","unix")
	if net_type == "unix":
		socket_fd = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
		sockname=config.get("network_socket","/var/spool/postfix/private/policy.sock")
		if os.path.exists(sockname):
			try:
				os.remove(sockname)
			except:
				logging.error("Error in removing socket file. Traceback: \n{0}\n".format(traceback.format_exc()))
				sys.exit(1)

		try:
			socket_fd.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
			socket_fd.bind(sockname)
		except:
			logging.error("Error in creating socket file. Traceback: \n{0}\n".format(traceback.format_exc()))
			sys.exit(1)

	elif net_type == "tcp":
		socket_fd = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		try:
			socket_fd.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
			socket_fd.bind((config.get("network_address","127.0.0.1"), int(config.get("network_port","7000"))))
		except:
			logging.error("Error in creating socket file. Traceback: \n{0}\n".format(traceback.format_exc()))
			sys.exit(1)

	try:
		socket_fd.setblocking(1)
		socket_fd.settimeout(None)
		socket_fd.listen(1)
	except:
		logging.error("Error in setting socket flags. Traceback: \n{0}\n".format(traceback.format_exc()))
		sys.exit(1)
	return socket_fd

def demonize():
	try: 
		pid = os.fork()
        except:
		logging.error("Error in first forking. Traceback: \n{0}\n".format(traceback.format_exc()))
		sys.exit(1)

	if pid > 0:
		sys.exit(0) 

	try:
		os.chdir("/") 
		os.setsid() 
		sys.stdin = open("/dev/null")
		sys.stderr = open("/dev/null","w")
		sys.stdout = open("/dev/null", "w")
	except:
		logging.error("Error in dropping control term. Traceback: \n{0}\n".format(traceback.format_exc()))
		sys.exit(1)

	try:
		pid = os.fork()
	except:
		logging.error("Error in second forking. Traceback: \n{0}\n".format(traceback.format_exc()))
		sys.exit(1)

	if pid > 0:
		sys.exit(0)

def write_pid(pid_file):
	pid = os.getpid()

	try:
		pid_file_desc = open(pid_file, "w")
		pid_file_desc.write(str(pid))
		pid_file_desc.close()
	except:
		logging.error("Error in creating pid file. Traceback: \n{0}\n".format(traceback.format_exc()))
		sys.exit(1)

def SIGINT_handler(pid_file, socket_fd, sql_pool, signum, frame):
	logging.info("Caught SIGNAL 2. Exiting...")

	if os.path.exists(pid_file):
		try:
			os.remove(pid_file)
		except:
			logging.error("Error in first forking. Traceback: \n{0}\n".format(traceback.format_exc()))


	try:
		socket_fd.shutdown(socket.SHUT_RDWR)
		socket_fd.close()
	except:
		logging.error("Error in closing master socket. Traceback: \n{0}\n".format(traceback.format_exc()))

	try:
		PySQLPool.terminatePool()
	except:
		logging.error("Error in terminating SQL pool. Traceback: \n{0}\n".format(traceback.format_exc()))
	sys.exit(0)
