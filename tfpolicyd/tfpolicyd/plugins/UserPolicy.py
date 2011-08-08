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

import Policy, threading, PySQLPool, subprocess, MySQLdb

class UserPolicy(Policy.Policy):
	def __init__(self, config, sql_pool):
		Policy.Policy.__init__(self, config, sql_pool)
		self._alias_maps  = self._postconf()
		self._sql_pool = sql_pool
		self._debug = False

		tmp_data = self._loadsql()
		if tmp_data:
			self._data = tmp_data
		else:
			self._data = {}

	def check(self, data):
		if data["request"] == "smtpd_access_policy":
			if data["sasl_username"] == "":
				sender = data["sender"]
				answer = self._check_one(data["recipient"], sender)
				if answer:
					return answer				
				else:
					array_of_recipients = self._postalias(data["recipient"])
					if array_of_recipients:
						recipients = list(set(array_of_recipients))
						for email in recipients:
							answer = self._check_one(email.lower(), Sender)
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
				if not self._check_one(data["sender"], data["recipient"]):
					self._train_one(data)

			elif data["action"] == "spam":
				if self._check_one(data["sender"], data["recipient"]):
					self._del_one(data)
			else:
				return None
		else:
			return None

	def _check_one(self, recipient, sender):
		result = None

		with self._mutex:
			if self._data.has_key(recipient) and self._data[recipient].has_key(sender):
				result = self._data[recipient][sender]

		return result

	def _postalias(self, recipient, deep = 1):

		if (deep > 50):
			return recipient

		post_alias = subprocess.Popen(["postalias -q {0} {1}".format(recipient, self._alias_maps )], shell = True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=None)
		output = post_alias.communicate()[0].strip().lower()
	        res = list()

		if output == recipient.lower().strip() or post_alias.returncode:
			return None
		else:
			test_mails = output.split(",")
			for email in test_mails:
				answer = self._postalias(email.strip(), deep + 1)
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
		return self._train_one(data , answer)

	def _train_one(self, data, answer = "dspam_innocent"):
		recipient = data["recipient"]
		sender = data["sender"]

		with self._mutex:
			if recipient != "" and sender != "":
				if not self._data.has_key(sender): self._data[sender] = {}
				
				if not self._data[sender].has_key(recipient):

					self._addrule(data, answer)
					self._data[sender][recipient] = answer

		return None

	def _del_one(self, data):

		recipient = data["recipient"]
		sender = data["sender"]

		with self._mutex:
			if recipient != "" and sender != "":

				if not self._data.has_key(sender): self._data[sender] = {}
				if self._data[sender].has_key(recipient):

					self._delrule(data)
					del self._data[sender][recipient]
		return None

	def _loadsql(self):
		try:
			sql_1 = "SELECT `id`,`username` FROM `users`"
			sql_2 = "SELECT `user_id`, `mail`, `accept` FROM `white_list_mail`"

			res={}
			users={}
			rules={}

			query = PySQLPool.getNewQuery(self._sql_pool, True)

			query.Query(sql_1)
			for row in query.record:
				tmp = row["username"].lower()
				users[str(int(row["id"]))] = tmp
				res[tmp] = {}

			query.Query(sql_2)
			for row in query.record:
				tmp = {}
				tmp[row["mail"].lower()] = row["accept"]
				if users.has_key(str(int(row["user_id"]))):
					res[users[str(int(row["user_id"]))]].update(tmp)

			return res
		except MySQLdb.Error as e:

			if self._debug:
				print e

			return None

	def _addrule(self, data, answer = "dspam_innocent"):
		if data["sasl_username"] != "" and data["sender"] != "" and data["recipient"] != "":
			try:
				sql_1 = "SELECT `id` FROM `users` WHERE `username` LIKE '{0}'"
				sql_2 = "INSERT IGNORE INTO `white_list_mail` VALUES(NULL, {0}, '{1}', '{2}')"

				query = PySQLPool.getNewQuery(self._sql_pool, True)

				query.Query(sql_1.format(data["sasl_username"]))
				try:
					tmp = str(int(query.record[0]["id"]))
				except IndexError as Err:
					return None

				query.Query(sql_2.format(tmp, data["recipient"], answer))
			except MySQLdb.Error as e:

			if self._debug:
				print e

			return None

	def _delrule(self, data):
		sql_1 = "SELECT `id` FROM `users` WHERE `username` LIKE '{0}'"
		sql_2 = "DELETE FROM `white_list_mail` WHERE `user_id` = '{0}' AND `mail` = '{1}'"

		if data["sender"] != "" and data["recipient"] != "":
			try:
				query = PySQLPool.getNewQuery(self._sql_pool, True)

				query.Query(sql_1.format(data["sender"]))
				try:
					tmp = str(int(query.record[0]["id"]))
				except IndexError as Err:
					return None

				query.Query(sql_2.format(tmp, data["recipient"]))
			except MySQLdb.Error as e:

			if self._debug:
				print e

			return None

	def reload(self):

		tmp_data = self._loadsql()

		if tmp_data:
			with self._mutex:
				self._data.clean()
				self._data.update(tmp_data)

		return None
