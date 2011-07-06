# -*- coding: utf-8 -*-
#
#		Some regexps for policyd
#       AnalysePolicy.py
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

import re

class cMailPart:
	def __init__(self):
		pass_
	def getuser(self, sMail):
		return self._oReMail.search(sMail).group("user")
	def getdomain(self, sMail):
		return self._oReMail.search(sMail).group("domain")

cMailPart._oReMail = re.compile(r"""(?P<user>[a-z0-9_.-\\*]+)@(?P<domain>(?:[a-z0-9-]+\.)+[a-z]{2,6})""", re.I | re.VERBOSE)
