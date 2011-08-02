# -*- coding: utf-8 -*-
#
#		Users filters for policyd
#       UserPolicy.py
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

import Policy, threading, PySQLPool, subprocess, ldap

class UserPolicy(Policy.Policy):
	def __init__(self, config, sql_pool):
		Policy.Policy.__init__(self, config, sql_pool)
		self._sql_pool = sql_pool
		self._config = config
		
		self.conf_aliases = self._postconf()
		self._users = self._loadldap()
		self._data = self._loadsql()

	def check(self, data):
		if data["request"] == "smtpd_access_policy":
			if data["sasl_username"] == "":
				sender = data["sender"]
				array_of_recipients = self._postalias(data["recipient"])
				answer = self._strict_check(data["recipient"], sender)
				if answer:
					return answer
				else:
					if recipient:
						recipient = list(set(array_of_recipients))
						for email in recipient:
							answer = self._strict_check(email.lower(), Sender)
							if answer: break

						if answer:
							return answer
						else:
							return None
					else:
						return None
			else:
				self.train(data)
				return None

		elif data["request"] == "junk_policy":

			if data["action"] == "notspam":
				if not self._strict_check(data["sender"], data["recipient"]):
					self._strict_train(data)

			elif data["action"] == "spam":
				if self._strict_check(data["sender"], data["recipient"]):
					self._strict_del(data)
			else:
				return None
		else:
			return None

	def _strict_check(self, recipient, sender):
		result = None

		with self._mutex:
			if self._data.has_key(recipient) and self._data[recipient].has_key(sender):
				result = self._data[recipient][sender]

		return None

	def _postalias(self, Recipient):
		post_alias = subprocess.Popen(["postalias -q {0} {1}".format(Recipient, self.ConfAliases)], shell = True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=None)
		output = post_alias.communicate()[0].strip().lower()
	        res = list()
		if output == recipient.lower().strip() or post_alias.returncode:
			return None
		else:
			test_mails = output.split(",")
			for email in test_mails:
				answer = self._postalias(email.strip())
				if answer:
					res += answer
				else:
					if not email in res:
						res.append(email.strip())

		return res

	def _postconf(self):
		post_conf = subprocess.Popen(["postconf -h virtual_alias_maps alias_maps"], shell = True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=None)
		conf = post_conf.communicate()[0].strip().replace("\n", " ").replace(",", "")
		return conf

	def train(self, data, answer = "dspam_innocent"):
		return self._strict_train(data , answer)

	def _strict_train(self, data, answer = "dspam_innocent"):
		recipient = data["recipient"]
		sender = data["sender"]

		with self.mutex:
			if recipient != "" and sender != "":
				if not self._data.has_key(sender): self._data[sender] = {}
				
				if not self._data[sender].has_key(recipient):

					self._addrule(data, self.sql_pool, answer)
					self._data[sender][recipient] = answer

		return None

	def _strict_del(self, data):

		recipient = data["recipient"]
		sender = data["sender"]

		with self.mutex:
			if recipient != "" and sender != "":

				if not self._data.has_key(sender): self._data[sender] = {}
				if self._data[sender].has_key(recipient):

					self._delrule(data, self.sql_pool)
					del self._data[sender][recipient]
		return None

	def _loadsql(sql_pool):
		sql_1 = "SELECT `user_id`, `mail`, `accept` FROM `white_list_mail`"

		res={}
		
		rules={}

		query = PySQLPool.getNewQuery(sql_pool, True)
		
		query.Query(sql_1)
		for row in query.record:
			tmp = {}
			tmp[row["mail"].lower()] = row["accept"]
			res[self._users[str(int(row["user_id"]))]].update(tmp)

		return res

	def _addrule(data, sql_pool, answer = "dspam_innocent"):
		if data["sasl_username"] != "" and data["sender"] != "" and data["recipient"] != "":

			sql_1 = "SELECT `id` FROM `users` WHERE `username` LIKE '{0}'"
			sql_2 = "INSERT IGNORE INTO `white_list_mail` VALUES(NULL, {0}, '{1}', '{2}')"

			query = PySQLPool.getNewQuery(sql_pool, True)

			query.Query(sql_1.format(data["sasl_username"]))
			try:
				tmp = str(int(query.record[0]["id"]))
			except IndexError as Err:
				return None

			query.Query(sql_2.format(tmp, data["recipient"], answer))

	def _delrule(data, sql_pool):
		sql_1 = "SELECT `id` FROM `users` WHERE `username` LIKE '{0}'"
		sql_2 = "DELETE FROM `white_list_mail` WHERE `user_id` = '{0}' AND `mail` = '{1}'"

		if data["sender"] != "" and data["recipient"] != "":
			query = PySQLPool.getNewQuery(sql_pool, True)

			query.Query(sql_1.format(data["sender"]))
			try:
				tmp = str(int(query.record[0]["id"]))
			except IndexError as Err:
				return None

			query.Query(sql_2.format(tmp, data["recipient"]))
