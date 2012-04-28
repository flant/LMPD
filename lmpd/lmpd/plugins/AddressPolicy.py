# -*- coding: utf-8 -*-
#
#       Address filters for LMPD (http://flant.ru/projects/lmpd)
#       AddressPolicy.py
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

import Policy, PySQLPool, traceback, logging, ipcalc

class AddressPolicy(Policy.Policy):
	def __init__(self, config, sql_pool, debug = False):
		Policy.Policy.__init__(self, config, sql_pool, debug)

		tmp_data = self._loadsql()
		if tmp_data:
			self._data_ipv4 = tmp_data[0]
			self._res_ipv4_sort_reversed = tmp_data[1]
			self._data_ipv6 = tmp_data[2]
			self._res_ipv6_sort_reversed = tmp_data[3]
			self._data_rdns = tmp_data[4]
		else:
			self._data_ipv4 = dict()
			self._res_ipv4_sort_reversed = list()
			self._data_ipv6 = dict()
			self._res_ipv6_sort_reversed = list()
			self._data_rdns = dict()

	def check(self, data):
		addr = data["client_address"]
		rdns = data["reverse_client_name"]

		tmp = self._check_ip(addr)
		if tmp:
			return tmp

		tmp = self._check_rdns(rdns)
		if tmp:
			return tmp

		return None

	def _loadsql(self):
		try:
			sql_1 = "SELECT `token`, `action` FROM `white_list_addr`"

			res_ipv4 = {}
			res_ipv6 = {}
			res_rdns = {}

			query = PySQLPool.getNewQuery(self._sql_pool, True)
			query.Query(sql_1)

			for row in query.record:
				rdns = False
				ip = None
				try:
					ip = ipcalc.IP(row["token"])
				except:
					rdns = True

				if rdns:
					res_rdns[row["token"]] = row["action"].lower()
				else:
					if ip == None:
						logging.warn("Error in data. Strange row: {0}\n".format(row["token"]))
						continue
					mask = self._digest(ip.mask)
					if ip.v == 4:
						if not res_ipv4.has_key(mask):
							res_ipv4[mask] = dict()
						res_ipv4[mask][int(ip.bin(),2) & mask] = row["action"]
					elif ip.v == 6:
						if not res_ipv6.has_key(mask):
							res_ipv6[mask] = dict()
						res_ipv6[mask][int(ip.bin(),2) & mask] = row["action"]
					else:
						logging.warn("Error in data. Strange row: {0}\n".format(row["token"]))
						continue

			return res_ipv4, sorted(res_ipv4.keys(), reverse=True), res_ipv6, sorted(res_ipv6.keys(), reverse=True), res_rdns
		except:
			if self._debug:
				logging.warn("Error in getting SQL data for Address policy. Traceback: \n{0}\n".format(traceback.format_exc()))

			return None

	def _check_ip(self, data):
		version = ipcalc.IP(data).v
		if version == 4:
			return self._check_ipv4(data)
		elif version == 6:
			return self._check_ipv6(data)
		else:
			return None

	def _check_ipv4(self, data):
		int_ip = int(ipcalc.IP(data).bin(), 2)
		for mask in self._res_ipv4_sort_reversed:
			net = int_ip & mask
			if self._data_ipv4[mask].has_key(net):
				return self._data_ipv4[mask][net]
		return None

	def _check_ipv6(self, data):
		int_ip = int(ipcalc.IP(data).bin(), 2)
		for mask in self._res_ipv6_sort_reversed:
			net = int_ip & mask
			if self._data_ipv6[mask].has_key(net):
				return self._data_ipv6[mask][net]
		return None

	def _check_rdns(self, subj):
		if self._data_rdns.has_key(subj):
			return self._data_rdns[subj]
		else:
			tmp_arr = subj.split('.')
			for iter in xrange(0, len(tmp_arr) + 1):
				check_dns = '.'.join(tmp_arr[iter:])
				if iter > 0 and self._data_rdns.has_key("."+check_dns):
					return self._data_rdns["."+check_dns]
		return None

	def _bits(self, i,n):
		return ''.join(map(str, list(tuple((0,1)[i>>j & 1] for j in xrange(n-1,-1,-1)))))

	def _digest(self, num):
		return int('1'*num+'0'*(32-num),2)

	def reload(self):

		tmp_data = self._loadsql()

		if tmp_data:
			self._data_ipv4 = tmp_data[0]
			self._res_ipv4_sort_reversed = tmp_data[1]
			self._data_ipv6 = tmp_data[2]
			self._res_ipv6_sort_reversed = tmp_data[3]
			self._data_rdns = tmp_data[4]
		else:
			self._data_ipv4 = dict()
			self._res_ipv4_sort_reversed = list()
			self._data_ipv6 = dict()
			self._res_ipv6_sort_reversed = list()
			self._data_rdns = dict()

		return None
