#Regexp module for policyd

import re

class cMailPart:
	def __init__(self):
		pass_
	def getuser(self, sMail):
		return self._oReMail.search(sMail).group("user")
	def getdomain(self, sMail):
		return self._oReMail.search(sMail).group("domain")

cMailPart._oReMail = re.compile(r"""(?P<user>[a-z0-9_.-\\*]+)@(?P<domain>(?:[a-z0-9-]+\.)+[a-z]{2,6})""", re.I | re.VERBOSE)
