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
	def __init__(self, Socket, ThreadName, Debug = False):
		dict.__init__(self)
		self.ThreadName = ThreadName
		self.Debug = Debug
		self.Conn_sock = Socket
		self._Tmp = str("")
		if self.Debug:
			self.StartTime = time.time()
			self.ProcessedMessages = 0
			self.LastMessageTime = self.StartTime
			self.TmpLogFile = open("./logs/" + self.ThreadName, "w")

	def __enter__(self):
		return self

	def __exit__(self, type, value, traceback):
		self.close()

	def _fReadSocket(self):
		Data = str("")

		while (True):

			if "\n\n" in self._Tmp:
				Str = self._Tmp.split("\n\n", 1)
				Data = Str[0]
				self._Tmp = Str[1]
				break

			try:
				self._Tmp += self.Conn_sock.recv(100)
			except socket.error as (errno, strerror):

				if self.Debug:
					print "socket.error error({0}): {1}".format(errno, strerror)
					print "Closing socket with error!"
					self.TmpLogFile.write("socket.error error({0}): {1}\n".format(errno, strerror))
					self.TmpLogFile.write("Closing socket with error!\n")

				return None

			if self.Debug:
				self.TmpLogFile.write("Read from socket in thread {0}, message {1}. Recieved data: {2}\n".format(self.ThreadName, self.ProcessedMessages + 1, self._Tmp))

			if not self._Tmp:

				if self.Debug:
					print "Closing socket with null answer"
					self.TmpLogFile.write("Closing socket with null answer\n")

				return None

		if self.Debug:
			self.LastMessageTime = time.time()
			self.ProcessedMessages += 1
			self.TmpLogFile.write("Get full message number {0}.\n\n\n".format(self.ProcessedMessages))

		return Data

	def answer(self, Data):
		try:
			self.Conn_sock.send("action={0}\n\n".format(Data))
		except socket.error as (errno, strerror):
			return False

		return True

	def close(self):
		if self.Debug:
			print "Closing socket now"
			self.TmpLogFile.write("Closing socket now\n")
			StopTime = time.time()
			print "Connection started {0}, stopped in {1}. Last message in {2}. Processe messages - {3}. Working {4} seconds.".format(time.strftime("%d.%m.%y - %H:%M:%S", time.localtime(self.StartTime)), time.strftime("%d.%m.%y - %H:%M:%S", time.localtime(StopTime)), time.strftime("%d.%m.%y - %H:%M:%S", time.localtime(self.LastMessageTime)), self.ProcessedMessages, (StopTime - self.StartTime))
			self.TmpLogFile.write("Connection started {0}, stopped in {1}. Last message in {2}. Processe messages - {3}. Working {4} seconds.\n\n".format(time.strftime("%d.%m.%y - %H:%M:%S", time.localtime(self.StartTime)), time.strftime("%d.%m.%y - %H:%M:%S", time.localtime(StopTime)), time.strftime("%d.%m.%y - %H:%M:%S", time.localtime(self.LastMessageTime)), self.ProcessedMessages, (StopTime - self.StartTime)))
		try:
			self.Conn_sock.shutdown(socket.SHUT_RDWR)
			self.Conn_sock.close()
		except socket.error as (errno, strerror):
			if self.Debug:
				print "socket.error error({0}): {1}".format(errno, strerror)
				self.TmpLogFile.write("socket.error error({0}): {1}".format(errno, strerror))
		if self.Debug:
			self.TmpLogFile.close()

	def get_message(self):
		if len(self) > 0: self.clear()
		Data = self._fReadSocket()
		if not Data: return False
		for key in self._ArrayOfRegexps:
			Tmp = self._ArrayOfRegexps[key].findall(Data)
			if len(Tmp) > 0:
				self[key] = Tmp[0].lower()
			else:
				self[key] = ""
		if self["request"] == "":
			raise ConnectionError('No request in Data line')
		return True

Connection._ArrayOfRegexps = {}
Connection._ArrayOfRegexps["request"] = re.compile(r"request=(.*?)\n", re.S) #0
Connection._ArrayOfRegexps["protocol_state"] = re.compile(r"protocol_state=(.*?)\n", re.S) #1
Connection._ArrayOfRegexps["client_address"] = re.compile(r"client_address=(.*?)\n", re.S) #2
Connection._ArrayOfRegexps["client_name"] = re.compile(r"client_name=(.*?)\n", re.S) #3
Connection._ArrayOfRegexps["reverse_client_name"] = re.compile(r"reverse_client_name=(.*?)\n", re.S) #4
Connection._ArrayOfRegexps["helo_name"] = re.compile(r"helo_name=(.*?)\n", re.S) #5
Connection._ArrayOfRegexps["sender"] = re.compile(r"sender=(.*?)\n", re.S) #6
Connection._ArrayOfRegexps["recipient"] = re.compile(r"recipient=(.*?)\n", re.S) #7
Connection._ArrayOfRegexps["sasl_method"]=re.compile(r"sasl_method=(.*?)\n", re.S) #8
Connection._ArrayOfRegexps["sasl_username"]=re.compile(r"sasl_username=(.*?)\n", re.S) #9
Connection._ArrayOfRegexps["sasl_sender"]=re.compile(r"sasl_sender=(.*?)\n", re.S) #10
Connection._ArrayOfRegexps["action"]=re.compile(r"action=(.*?)\n", re.S) #11
