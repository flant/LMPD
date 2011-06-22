#Regexp module for policyd

import re

class cParser(dict):
	oRegs = {}
	def __init__(self,sData):
		dict.__init__(self)
		if len(self.__class__.oRegs) == 0:
			self.__class__.oRegs = self.__fCreateRegex()
		self.sData = sData
		for key in self.__class__.oRegs:
			self[key] = self.__class__.oRegs[key].findall(self.sData)[0]
	def __fCreateRegex(self):
		oArr = {}
		oArr["protocol_state"] = re.compile(r"protocol_state=(.*?)\n", re.S) #0
		oArr["client_address"] = re.compile(r"client_address=(.*?)\n", re.S) #1
		oArr["client_name"] = re.compile(r"client_name=(.*?)\n", re.S) #2
		oArr["reverse_client_name"] = re.compile(r"reverse_client_name=(.*?)\n", re.S) #3
		oArr["helo_name"] = re.compile(r"helo_name=(.*?)\n", re.S) #4
		oArr["sender"] = re.compile(r"sender=(.*?)\n", re.S) #5
		oArr["recipient"] = re.compile(r"recipient=(.*?)\n", re.S) #6
		return oArr

class cMailPart:
	oReMail = 0
	def __init__(self):
		if self.__class__.oReMail == 0:
			self.__class__.oReMail = re.compile(r"""(?P<user>[a-z0-9_.-\\*]+)@(?P<domain>(?:[a-z0-9-]+\.)+[a-z]{2,6})""", re.I | re.VERBOSE)
	def getuser(self, sMail):
		return self.__class__.oReMail.search(sMail).group("user")
	def getdomain(self, sMail):
		return self.__class__.oReMail.search(sMail).group("domain")
