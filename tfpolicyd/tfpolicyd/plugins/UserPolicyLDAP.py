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

import Policy, threading, PySQLPool, subprocess, ldap, MySQLdb

class UserPolicyLDAP(Policy.Policy):
	def __init__(self, config, sql_pool):
		Policy.Policy.__init__(self, config, sql_pool)

		self._alias_maps  = self._postconf()
		self._sql_pool = sql_pool

		self._debug = False

		self._ldap_uri = config.get("filters_UserPolicyLDAP_ldap_addr", "ldaps://127.0.0.1")

		self._ldap_user = config.get("filters_UserPolicyLDAP_ldap_user", "cn=mail,ou=main,dc=acmeinc,dc=en")
		self._ldap_pass = config.get("filters_UserPolicyLDAP_ldap_pass", "")
		self._ldap_base_dn = config.get("filters_UserPolicyLDAP_ldap_base_dn", "dc=acmeinc,dc=en")
		self._ldap_mail_attr = config.get("filters_UserPolicyLDAP_ldap_mail_attr", "mail")
		self._ldap_id_attr = config.get("filters_UserPolicyLDAP_ldap_id_attr", "id")
		self._ldap_search_filter = config.get("filters_UserPolicyLDAP_ldap_search_filter", "(&(objectClass=Account)(mail=*))")

		self._mail_users, self._uid_users = self._loadldap()

		if self._mail_users:
			tmp_data = self._loadsql()
			if tmp_data:
				self._data = tmp_data
			else:
				self._data = {}
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

	def _loadsql(self, users):
		try:
			sql_1 = "SELECT `user_id`, `mail`, `accept` FROM `white_list_mail`"

			res={}
			rules={}

			for uid in users:
				res[users[uid]] = {}

			query = PySQLPool.getNewQuery(self._sql_pool, True)

			query.Query(sql_1)
			for row in query.record:
				tmp = {}
				tmp[row["mail"].lower()] = row["accept"]
				if users.has_key(str(int(row["user_id"]))):
					res[users[str(int(row["user_id"]))]].update(tmp)

			return res
		except MySQLError as e:

			if self._debug:
				print e

			return None

	def _loadldap(self):
		result_mail_set = {}
		result_uid_set = {}
		try:
			ldap_conn = ldap.open(self._ldap_uri)
			ldap_conn.protocol_version = ldap.VERSION3
			ldap_conn.simple_bind_s(self._ldap_user, self._ldap_pass)
		except ldap.LDAPError, e:
			return None, None

		try:
			ldap_result_id = ldap_conn.search(self._ldap_base_dn, ldap.SCOPE_SUBTREE, self._ldap_search_filter, [self._ldap_mail_attr,self._ldap_id_attr])
			while (True):
				result_type, result_data = ldap_conn.result(ldap_result_id, 0)
				if (result_data == []):
					break
				else:
					if result_type == ldap.RES_SEARCH_ENTRY:
						result_mail_set[result_data[0][1][self._ldap_id_attr][0]] = result_data[0][1][self._ldap_mail_attr][0]
						result_uid_set[result_data[0][1][self._ldap_mail_attr][0]] = result_data[0][1][self._ldap_id_attr][0]
		except ldap.LDAPError, e:
			return None, None

		ldap_conn.unbind_s()

		return result_mail_set, result_uid_set

	def _addrule(self, data, answer = "dspam_innocent"):
		if data["sasl_username"] != "" and data["sender"] != "" and data["recipient"] != "":

			sql_1 = "INSERT IGNORE INTO `white_list_mail` VALUES(NULL, {0}, '{1}', '{2}')"
			try:
				query = PySQLPool.getNewQuery(self._sql_pool, True)

				if self._uid_users.has_key(data["sasl_username"]):
					tmp = self._uid_users[data["sasl_username"]]
					query.Query(sql_1.format(tmp, data["recipient"], answer))
			except MySQLError as e:

				if self._debug:
					print e

				return None

	def _delrule(self, data):
		sql_1 = "DELETE FROM `white_list_mail` WHERE `user_id` = '{0}' AND `mail` = '{1}'"

		if data["sasl_username"] != "" and data["sender"] != "" and data["recipient"] != "":
			try:
				query = PySQLPool.getNewQuery(self._sql_pool, True)

				if self._uid_users.has_key(data["sasl_username"]):
					tmp = self._uid_users[data["sasl_username"]]
					query.Query(sql_1.format(tmp, data["recipient"]))
			except MySQLError as e:

				if self._debug:
					print e

				return None
			
	def reload(self):

		tmp_users, tmp_uids = self._loadldap()
		if tmp_users:
			tmp_data = self._loadsql(tmp_users)
		else:
			tmp_data = {}

		if tmp_data and tmp_uids:
			with self._mutex:
				self._data.clean()
				self._data.update(tmp_data)
				self._mail_users.clean()
				self._mail_users.update(tmp_users)
				self._uid_users.clean()
				self._uid_users.update(tmp_uids)

		return None
