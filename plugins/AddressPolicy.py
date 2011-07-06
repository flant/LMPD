# -*- coding: utf-8 -*-
#
#		Address filters for policyd
#       AddressPolicy.py
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

import Policy, threading, PySQLPool

def loadsql(oSqlPool):
	sSql_1 = "SELECT `mx_addr`, `accept` FROM `white_list_addr`"
	aRes = {}

	query = PySQLPool.getNewQuery(oSqlPool, True)
	query.Query(sSql_1)		

	for row in query.record:
		aRes[row[0]] = row[1].lower()

	return aRes
#Dont need now
#def addrule(oData, oSqlPool):
#	sSql_1 = "INSERT INTO `white_list_addr` VALUES(NULL, {0}, {1})"
#
#	oSqlConn.execute(sSql_1.format(oData["address"], oData["answer"]))

class AddressPolicy(Policy.Policy):
	def __init__(self, aData, oSqlPool):
		self.mutex = threading.Lock()
		Policy.Policy.__init__(self, aData, oSqlPool)

	def check(self, oData):
		sAddr = oData["client_address"]
		if self.aData.has_key(sAddr):
			return self.aData[sAddr]
		else:
			return None
