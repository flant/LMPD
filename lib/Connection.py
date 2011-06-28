#Postfix Protocol class for policyd

import socket, re

class ConnectionError(Exception):
	def __init__(self, value):
		self.value = value

	def __str__(self):
		return 'Error: ' + self.value

class Connection(dict):
	def __init__(self, oSocket):
		dict.__init__(self)
		self.oConn_sock = oSocket

	def __enter__(self):
		return self

	def __exit__(self, type, value, traceback):
		self.close()

	def _fReadSocket(self):
		sData = str("")
		while 1:
			sTmp = self.oConn_sock.recv(100)
			if not sTmp: return None
			sData += sTmp
			if "\n\n" in sTmp:
				break
		return sData

	def answer(self, sData):
		self.oConn_sock.send("action={0}\n\n".format(sData))

	def close(self):
		self.oConn_sock.close()

	def get_message(self):
		if len(self) > 0: self.clear()
		sData = self._fReadSocket()
		if not sData: return False
		for key in self._oArr:
			aTmp = self._oArr[key].findall(sData)
			if len(aTmp) > 0:
				self[key] = aTmp[0]
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
