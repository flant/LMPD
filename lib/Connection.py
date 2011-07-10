# -*- coding: utf-8 -*-
#
#		Postfix Protocol class for policyd
#       Connection.py
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

import socket, re, time

class ConnectionError(Exception):
	def __init__(self, value):
		self.value = value

	def __str__(self):
		return 'Error: ' + self.value

class Connection(dict):
	def __init__(self, oSocket, ThreadName, Debug = False):
		dict.__init__(self)
		self.ThreadName = ThreadName
		self.Debug = Debug
		self.oConn_sock = oSocket
		self._sTmp = str("")
		if self.Debug:
			self.starttime = time.time()
			self.ms = 0
			self.lm = self.starttime
			self.TmpLogFile = open("./logs/" + self.ThreadName, "w")

	def __enter__(self):
		return self

	def __exit__(self, type, value, traceback):
		self.close()

	def _fReadSocket(self):
		sData = str("")

		while (True):

			if "\n\n" in self._sTmp:
				aStr = self._sTmp.split("\n\n", 1)
				sData += aStr[0]
				self._sTmp = aStr[1]
				break
			else:
				sData += self._sTmp

			try:
				self._sTmp = self.oConn_sock.recv(100)
			except socket.error as (errno, strerror):
				if self.Debug:
					print "socket.error error({0}): {1}".format(errno, strerror)
					print "Closing socket with error!"
					self.TmpLogFile.write("socket.error error({0}): {1}".format(errno, strerror))
					self.TmpLogFile.write("Closing socket with error!")
				return None

			if self.Debug:
				self.TmpLogFile.write("Read from socket in thread {0}, message {1}. Recieved data: {2}".format(self.ThreadName, self.ms + 1, self._sTmp))

			if not self._sTmp:
				if self.Debug:
					print "Closing socket with null answer"
					self.TmpLogFile.write("Closing socket with null answer")
				return None
		if self.Debug:
			self.lm = time.time()
			self.ms += 1
		return sData

	def answer(self, sData):
		try:
			self.oConn_sock.send("action={0}\n\n".format(sData))
		except socket.error as (errno, strerror):
			return False

		return True

	def close(self):
		if self.Debug:
			print "Closing socket now"
			self.TmpLogFile.write("Closing socket now")
			stoptime = time.time()
			print "Connection started {0}, stopped in {1}. Last message in {2}. Processe messages - {3}. Working {4} seconds.".format(time.strftime("%d.%m.%y - %H:%M:%S", time.localtime(self.starttime)), time.strftime("%d.%m.%y - %H:%M:%S", time.localtime(stoptime)), time.strftime("%d.%m.%y - %H:%M:%S", time.localtime(self.lm)), self.ms, (stoptime - self.starttime))
			self.TmpLogFile.write("Connection started {0}, stopped in {1}. Last message in {2}. Processe messages - {3}. Working {4} seconds.".format(time.strftime("%d.%m.%y - %H:%M:%S", time.localtime(self.starttime)), time.strftime("%d.%m.%y - %H:%M:%S", time.localtime(stoptime)), time.strftime("%d.%m.%y - %H:%M:%S", time.localtime(self.lm)), self.ms, (stoptime - self.starttime)))
		try:
			self.oConn_sock.shutdown(socket.SHUT_RDWR)
			self.oConn_sock.close()
		except socket.error as (errno, strerror):
			if self.Debug:
				print "socket.error error({0}): {1}".format(errno, strerror)
			pass

	def get_message(self):
		if len(self) > 0: self.clear()
		sData = self._fReadSocket()
		if not sData: return False
		for key in self._oArr:
			aTmp = self._oArr[key].findall(sData)
			if len(aTmp) > 0:
				self[key] = aTmp[0].lower()
			else:
				self[key] = ""
		if self["request"] == "":
			raise ConnectionError('No request in Data line')
		return True

Connection._oArr = {}
Connection._oArr["request"] = re.compile(r"request=(.*?)\n", re.S) #0
Connection._oArr["protocol_state"] = re.compile(r"protocol_state=(.*?)\n", re.S) #1
Connection._oArr["client_address"] = re.compile(r"client_address=(.*?)\n", re.S) #2
Connection._oArr["client_name"] = re.compile(r"client_name=(.*?)\n", re.S) #3
Connection._oArr["reverse_client_name"] = re.compile(r"reverse_client_name=(.*?)\n", re.S) #4
Connection._oArr["helo_name"] = re.compile(r"helo_name=(.*?)\n", re.S) #5
Connection._oArr["sender"] = re.compile(r"sender=(.*?)\n", re.S) #6
Connection._oArr["recipient"] = re.compile(r"recipient=(.*?)\n", re.S) #7
Connection._oArr["sasl_method"]=re.compile(r"sasl_method=(.*?)\n", re.S) #8
Connection._oArr["sasl_username"]=re.compile(r"sasl_username=(.*?)\n", re.S) #9
Connection._oArr["sasl_sender"]=re.compile(r"sasl_sender=(.*?)\n", re.S) #10
