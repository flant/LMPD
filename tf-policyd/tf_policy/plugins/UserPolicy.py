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

import Policy, threading, PySQLPool, subprocess

def loadsql(sql_pool):
	sql_1 = "SELECT `id`,`username` FROM `users`"
	sql_2 = "SELECT `user_id`, `mail`, `accept` FROM `white_list_mail`"

	res={}
	users={}
	rules={}
	
	query = PySQLPool.getNewQuery(sql_pool, True)

	query.Query(sql_1)
	for row in query.record:
		tmp = row["username"].lower()
		users[str(int(row["id"]))] = tmp
		res[Tmp] = {}

	query.Query(sql_2)
	for row in query.record:
		tmp = {}
		tmp[row["mail"].lower()] = row["accept"]
		res[users[str(int(row["user_id"]))]].update(tmp)

	return res

def addrule(data, sql_pool, answer = "dspam_innocent"):
	if data["sasl_username"] != "" and data["sender"] != "" and data["recipient"] != "":

		sql_1 = "SELECT `id` FROM `users` WHERE `username` LIKE '{0}'"
		sql_2 = "INSERT IGNORE INTO `white_list_mail` VALUES(NULL, {0}, '{1}', '{2}')"

		query = PySQLPool.getNewQuery(sql_pool, True)

		query.Query(sql_1.format(data["sasl_username"]))
		try:
			Tmp = str(int(query.record[0]["id"]))
		except IndexError as Err:
			return None

		query.Query(sql_2.format(tmp, data["recipient"], answer))

def delrule(data, sql_pool):
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

class UserPolicy(Policy.Policy):
	def __init__(self, data, sql_pool):
		self.mutex = threading.Lock()
		Policy.Policy.__init__(self, data, sql_pool)
		self.conf_aliases = self._postconf()

	def check(self, data):
		if Data["request"] == "smtpd_access_policy":
			if Data["sasl_username"] == "":
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
		if self.data.has_key(recipient) and self.Data[recipient].has_key(sender):
			return self.data[recipient][sender]
		else:
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
				if not self.data.has_key(sender): self.Data[sender] = {}
				
				if not self.data[sender].has_key(recipient):

					addrule(data, self.sql_pool, answer)
					self.data[sender][secipient] = answer

		return None

	def _strict_del(self, data):

		recipient = data["recipient"]
		sender = data["sender"]

		with self.mutex:
			if recipient != "" and sender != "":

				if not self.data.has_key(sender): self.data[sender] = {}
				if self.data[sender].has_key(recipient):

					delrule(data, self.sql_pool)
					del self.data[sender][recipient]
		return None
