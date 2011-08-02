# -*- coding: utf-8 -*-
#
#		Domain filters for policyd
#       DomainPolicy.py
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

def loadsql(sql_pool):
	sql_1 = "SELECT `dns`, `accept` FROM `white_list_dns`"
	res = {}

	query = PySQLPool.getNewQuery(sql_pool, True)
	query.Query(sql_1)
			
	for row in query.record:
		res[row[0]] = row[1].lower()
			
	return res

#Dont need now
#def addrule(oData, oSqlConn):
#	sSql_1 = "INSERT INTO `white_list_dns` VALUES(NULL, {0}, {1})"
#
#	oSqlConn.execute(sSql_1.format(oData["helo_name"], oData["answer"]))

class DomainPolicy(Policy.Policy):
	def __init__(self, data, sql_pool):
		self.mutex = threading.Lock()
		Policy.Policy.__init__(self, data, sql_pool)

	def check(self, data):
		domain = data["helo_name"]
		if self.data.has_key(domain):
			return self.data[domain]
		else:
			return None
