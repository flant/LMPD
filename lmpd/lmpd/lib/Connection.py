# -*- coding: utf-8 -*-
#
#       Postfix Protocol class for lmpd
#       Connection.py
#       
#       Copyright (C) 2009-2011 CJSC Flant (www.flant.ru)
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

import socket, re, time, traceback, logging

class ConnectionError(Exception):
	def __init__(self, value):
		self.value = value

	def __str__(self):
		return 'Error: ' + self.value

class Connection(dict):
	def __init__(self, socket, thread_name, debug = False):
		dict.__init__(self)
		self.thread_name = thread_name
		self.debug = debug
		self.socket = socket
		self._buffer = str("")
		if self.debug:
			self.start_time = time.time()
			self.processed_messages = 0
			self.last_message_time = self.start_time

	def __enter__(self):
		return self

	def __exit__(self, type, value, traceback):
		self.close()

	def _read_socket(self):
		data = ""

		while (True):

			if "\n\n" in self._buffer:
				array_str = self._buffer.split("\n\n", 1)
				data = array_str[0] + "\n\n"
				self._buffer = array_str[1]
				break

			try:
				self._buffer += self.socket.recv(100)

			except:

				if self.debug:
					logging.error("Error, while reading socket. Traceback:\n{0}".format(traceback.format_exc()))
				logging.warn("Closing socket with error!")

				return None

			if not self._buffer:

				if self.debug:
					logging.debug("Closing socket with null answer")

				return None

		if self.debug:
			self.last_message_time = time.time()
			self.processed_messages += 1

		return data

	def answer(self, data):
		try:
			self.socket.send("action={0}\n\n".format(data))
		except:
			if self.debug:
				logging.error("Error, while reading socket. Traceback:\n{0}".format(traceback.format_exc()))
			logging.warn("Cannot send data though socket!")
			return False

		return True

	def close(self):
		logging.info("Closing socket now")
		if self.debug:
			stop_time = time.time()
			logging.debug("Connection started {0}, stopped in {1}. Last message in {2}. Processe messages - {3}. Working {4} seconds.".format(time.strftime("%d.%m.%y - %H:%M:%S", time.localtime(self.start_time)), time.strftime("%d.%m.%y - %H:%M:%S", time.localtime(stop_time)), time.strftime("%d.%m.%y - %H:%M:%S", time.localtime(self.last_message_time)), self.processed_messages, (stop_time - self.start_time)))
		try:
			self.socket.shutdown(socket.SHUT_RDWR)
			self.socket.close()
		except:
			if self.debug:
				logging.debug("Error, while cloasing socket. Tracaback: {0}".format(traceback..format_exc()))

	def get_message(self):

		if len(self) > 0: self.clear()

		data = self._read_socket()

		if not data: return False

		for key in self._array_of_regexps:
			tmp = self._array_of_regexps[key].findall(data)
			if len(tmp) > 0:
				self[key] = tmp[0].lower()
			else:
				self[key] = ""

		if self["request"] == "":
			raise ConnectionError('No request in Data line')
		return True

Connection._array_of_regexps = {}
Connection._array_of_regexps["request"] = re.compile(r"request=(.*?)\n", re.S) #0
Connection._array_of_regexps["protocol_state"] = re.compile(r"protocol_state=(.*?)\n", re.S) #1
Connection._array_of_regexps["client_address"] = re.compile(r"client_address=(.*?)\n", re.S) #2
Connection._array_of_regexps["client_name"] = re.compile(r"client_name=(.*?)\n", re.S) #3
Connection._array_of_regexps["reverse_client_name"] = re.compile(r"reverse_client_name=(.*?)\n", re.S) #4
Connection._array_of_regexps["helo_name"] = re.compile(r"helo_name=(.*?)\n", re.S) #5
Connection._array_of_regexps["sender"] = re.compile(r"sender=(.*?)\n", re.S) #6
Connection._array_of_regexps["recipient"] = re.compile(r"recipient=(.*?)\n", re.S) #7
Connection._array_of_regexps["sasl_method"]=re.compile(r"sasl_method=(.*?)\n", re.S) #8
Connection._array_of_regexps["sasl_username"]=re.compile(r"sasl_username=(.*?)\n", re.S) #9
Connection._array_of_regexps["sasl_sender"]=re.compile(r"sasl_sender=(.*?)\n", re.S) #10
Connection._array_of_regexps["action"]=re.compile(r"action=(.*?)\n", re.S) #11
