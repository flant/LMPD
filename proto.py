#Protocol class for policyd

import socket

class cPRProtocol():
	def __init__(self,oSocket):
		self.oConn_sock = oSocket
	def getdata(self):
		return self.__fReadSocket()
	def __fReadSocket(self):
		sData = str("")
		while 1:
			sTmp = self.oConn_sock.recv(100)
			sData += sTmp
			if "\n\n" in sTmp:
				break
		return sData
	def answer(self, sData):
		self.oConn_sock.send("answer={0}\n\n".format(sData))
	def __del__(self):
		self.oConn_sock.close()
