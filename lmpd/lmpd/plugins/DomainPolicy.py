# -*- coding: utf-8 -*-
#
#       Domain filters for LMPD (http://flant.ru/projects/lmpd)
#       DomainPolicy.py
#       
#       Copyright (C) 2009-2012 CJSC Flant (www.flant.ru)
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

import Policy, PySQLPool, traceback, logging

class DomainPolicy(Policy.Policy):
	def __init__(self, config, sql_pool, debug = False):
		Policy.Policy.__init__(self, config, sql_pool, debug)
		self._sql_pool = sql_pool

		tmp_data = self._loadsql()
		if tmp_data:
			self._data = tmp_data
		else:
			self._data = {}

	def check(self, data):
		subj = data["sender"]
		if self._data.has_key(data):
			return self._data[subj]
		else:
			tmp_dns = subj.split('@')[-1]
			tmp_arr = tmp_dns.split('.')
			tmp_str = ""
			if self._data.has_key(tmp_dns):
					return self._data[tmp_dns]
			for iter in xrange(0, len(tmp_arr) + 1):
				check_dns = '.'.join(tmp_arr[iter:])
				if iter > 0 and self._data.has_key("."+check_dns):
					return self._data["."+check_dns]
		return None

	def _loadsql(self):
		try:
			sql_1 = "SELECT `token`, `action` FROM `white_list_email`"
			res = {}

			query = PySQLPool.getNewQuery(self._sql_pool, True)
			query.Query(sql_1)
			
			for row in query.record:
				res[row["token"]] = row["action"].lower()

			return res

		except:
			if self._debug:
				logging.warn("Error in getting SQL data for Domain policy. Traceback: \n{0}\n".format(traceback.format_exc()))
			return None

	def reload(self):

		tmp_data = self._loadsql()

		if tmp_data:
			self._data.clear()
			self._data.update(tmp_data)

		return None
