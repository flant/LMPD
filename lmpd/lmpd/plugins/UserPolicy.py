# -*- coding: utf-8 -*-
#
#       Users filters for LMPD (http://flant.ru/projects/lmpd)
#       UserPolicy.py
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

import Policy, PySQLPool, subprocess, traceback, logging
from string import lower

class UserPolicy(Policy.Policy):
	def __init__(self, config, sql_pool, debug = False):
		Policy.Policy.__init__(self, config, sql_pool, debug)
		self._alias_maps  = self._postconf()
		self._keep_rules = config.get("filters_keep", True)
                self._exclude_mails = config.get("filters_exclude", list())
		map(lower, self._exclude_mails)

		tmp_data = self._loadsql()
		if tmp_data:
			self._data = tmp_data
		else:
			self._data = {}

	def check(self, data):
		if (data["sender"] in self._exclude_mails) or (data["recipient"] in self._exclude_mails):
			return None
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
							answer = self._check_one(email.lower(), sender)
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

		if self._data.has_key(recipient) and self._data[recipient].has_key(sender):
			result = self._data[recipient][sender]

		return result

	def _postalias(self, recipient, deep = 1):

		if (deep > 50):
			return recipient

		try:
			post_alias = subprocess.Popen(["postalias -q {0} {1}".format(recipient, self._alias_maps )], shell = True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=None)
		except:
			logging.warn("Error in getting alias data for User policy. Traceback: \n{0}\n".format(traceback.format_exc()))
			return None

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
		try:
			post_conf = subprocess.Popen(["postconf -h virtual_alias_maps alias_maps"], shell = True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=None)
		except:
			logging.error("Error in getting postconf data for User policy. Traceback: \n{0}\n".format(traceback.format_exc()))
			raise BaseException('Postconf error')

		conf = post_conf.communicate()[0].strip().replace("\n", " ").replace(",", "")
		return conf

	def train(self, data, answer = "dspam_innocent"):
		return self._train_one(data , answer)

	def _train_one(self, data, answer = "dspam_innocent"):
		recipient = data["recipient"]
		sender = data["sender"]

		if recipient != "" and sender != "":
			if not self._data.has_key(sender): self._data[sender] = {}

			if not self._data[sender].has_key(recipient):
				if self._addrule(data, answer):
					self._data[sender][recipient] = answer

		return None

	def _del_one(self, data):

		recipient = data["recipient"]
		sender = data["sender"]

		if recipient != "" and sender != "":
			if not self._data.has_key(sender): self._data[sender] = {}
			if self._data[sender].has_key(recipient):
				if self._delrule(data):
					del self._data[sender][recipient]

		return None

	def _loadsql(self):
		try:
			sql_1 = 'SELECT `white_list_users`.`id`, `users`.`username`, `white_list_users`.`token`, `white_list_users`.`action` FROM `users` RIGHT JOIN `white_list_users` ON `users`.`id` = `white_list_users`.`user_id`'
			sql_2 = 'DELETE FROM `white_list_users` WHERE `id` = {0}'

			res={}
			users={}
			rules={}
			clean_rulse=list()

			query = PySQLPool.getNewQuery(self._sql_pool, True)

			query.Query(sql_1)
			for row in query.record:
				if not self._keep_rules and row["username"] == None:
					clean_rulse.append(int(row["id"]))
				if row["username"] == None:
					continue
				if row["username"].lower() in self._exclude_mails:
					continue
				if not res.has_key(row["username"].lower()):
					res[row["username"].lower()] = dict()
				res[row["username"].lower()][row["token"].lower()] = row["action"]

			for iter in clean_rulse:
				query.Query(sql_2.format(iter))

			return res
		except:
			if self._debug:
				logging.debug("Error in getting SQL data for User policy. Traceback: \n{0}\n".format(traceback.format_exc()))

			return None

	def _addrule(self, data, answer = "dspam_innocent"):
		if data["sasl_username"] != "" and data["sender"] != "" and data["recipient"] != "":
			try:
				sql = 'INSERT IGNORE INTO `white_list_users` (`white_list_users`.`user_id`, `white_list_users`.`token`, `white_list_users`.`action`) SELECT `id` AS `userid`, \'{0}\' AS `token`, \'{1}\' AS `action` FROM `users` WHERE `users`.`username` LIKE \'{2}\';'

				query = PySQLPool.getNewQuery(self._sql_pool, True)

				query.Query(sql.format(data["recipient"], answer, data["sasl_username"]))
				return True
			except:
				logging.warn("Error in creating a rule for UserLdap policy. Traceback: \n{0}\n".format(traceback.format_exc()))
				return False

	def _delrule(self, data):

		sql = 'DELETE FROM `white_list_users` WHERE `token` LIKE \'{0}\' AND `user_id` IN (SELECT `id` AS `user_id` FROM `users` WHERE `username` LIKE \'{1}\' )'

		if data["sender"] != "" and data["recipient"] != "":
			try:
				query = PySQLPool.getNewQuery(self._sql_pool, True)

				query.Query(sql.format(data["recipient"], data["sender"]))

				return True
			except:
				logging.warn("Error in deleting a rule for UserLdap policy. Traceback: \n{0}\n".format(traceback.format_exc()))
				return False

	def reload(self):

		tmp_data = self._loadsql()

		if tmp_data:
			self._data.clear()
			self._data.update(tmp_data)

		return None
