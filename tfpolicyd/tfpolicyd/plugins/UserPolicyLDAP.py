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

class UserPolicyLDAP(Policy.Policy):
	def __init__(self, config, sql_pool):
		Policy.Policy.__init__(self, config, sql_pool)

		self.conf_aliases = self._postconf()
		self._sql_pool = sql_pool
		self._ldap_addr = config.get("filters_UserPolicyLDAP_ldap_addr", "127.0.0.1")

		if config.get("filters_UserPolicyLDAP_ldap_proto_ver", None):
			self._ldap_proto_ver = ldap.VERSION3
		else:
			self._ldap_proto_ver = ldap.VERSION2

		self._ldap_user = config.get("filters_UserPolicyLDAP_ldap_user", "cn=mail,ou=main,dc=acmeinc,dc=en")
		self._ldap_pass = config.get("filters_UserPolicyLDAP_ldap_pass", "")
		self._ldap_base_dn = config.get("filters_UserPolicyLDAP_ldap_base_dn", "dc=acmeinc,dc=en")
		self._ldap_retrieve_attributes = config.get("filters_UserPolicyLDAP_ldap_retrieve_attributes", ["mail", "uidNumber"])
		self._ldap_search_filter = config.get("filters_UserPolicyLDAP_ldap_search_filter", "(&(objectClass=Account)(mail=*))")

		self._mail_users, self._uid_users = self._loadldap()

		if self._mail_users:
			self._data = self._loadsql(self._mail_users)
		else:
			self._data = {}

	def check(self, data):
		if data["request"] == "smtpd_access_policy":
			if data["sasl_username"] == "":
				sender = data["sender"]
				answer = self._strict_check(data["recipient"], sender)
				if answer:
					return answer				
				else:
					array_of_recipients = self._postalias(data["recipient"])
					if array_of_recipients:
						recipients = list(set(array_of_recipients))
						for email in recipients:
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

		return result

	def _postalias(self, recipient, deep = 1):

		if (deep > 50):
			return recipient

		post_alias = subprocess.Popen(["postalias -q {0} {1}".format(recipient, self.conf_aliases)], shell = True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=None)
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
		return self._strict_train(data , answer)

	def _strict_train(self, data, answer = "dspam_innocent"):
		recipient = data["recipient"]
		sender = data["sender"]

		with self._mutex:
			if recipient != "" and sender != "":
				if not self._data.has_key(sender): self._data[sender] = {}
				
				if not self._data[sender].has_key(recipient):

					self._addrule(data, answer)
					self._data[sender][recipient] = answer

		return None

	def _strict_del(self, data):

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

	def _loadldap(self):
		result_mail_set = {}
		result_uid_set = {}
		try:
			ldap_conn = ldap.open(self._ldap_addr)
			ldap_conn.protocol_version = self._ldap_proto_ver
			ldap_conn.simple_bind_s(self._ldap_user, self._ldap_pass)
		except ldap.LDAPError, e:
			return None, None

		baseDN = self._ldap_base_dn
		searchScope = ldap.SCOPE_SUBTREE
		retrieveAttributes = self._ldap_retrieve_attributes
		searchFilter = self._ldap_search_filter

		try:
			ldap_result_id = ldap_conn.search(baseDN, searchScope, searchFilter, retrieveAttributes)
			while 1:
				result_type, result_data = ldap_conn.result(ldap_result_id, 0)
				if (result_data == []):
					break
				else:
					if result_type == ldap.RES_SEARCH_ENTRY:
						result_mail_set[result_data[0][1][retrieveAttributes[1]][0]] = result_data[0][1][retrieveAttributes[0]][0]
						result_uid_set[result_data[0][1][retrieveAttributes[0]][0]] = result_data[0][1][retrieveAttributes[1]][0]
		except ldap.LDAPError, e:
			return None, None

		return result_mail_set, result_uid_set

	def _addrule(self, data, answer = "dspam_innocent"):
		if data["sasl_username"] != "" and data["sender"] != "" and data["recipient"] != "":

			sql_1 = "INSERT IGNORE INTO `white_list_mail` VALUES(NULL, {0}, '{1}', '{2}')"

			query = PySQLPool.getNewQuery(self._sql_pool, True)

			if self._uid_users.has_key(data["sasl_username"]):
				tmp = self._uid_users[data["sasl_username"]]
				query.Query(sql_1.format(tmp, data["recipient"], answer))

	def _delrule(self, data):
		sql_1 = "DELETE FROM `white_list_mail` WHERE `user_id` = '{0}' AND `mail` = '{1}'"

		if data["sasl_username"] != "" and data["sender"] != "" and data["recipient"] != "":
			query = PySQLPool.getNewQuery(self._sql_pool, True)

			if self._uid_users.has_key(data["sasl_username"]):
				tmp = self._uid_users[data["sasl_username"]]
				query.Query(sql_1.format(tmp, data["recipient"]))

	def reload(self):

		tmp_users = self._loadldap()
		tmp_data = self._loadsql(tmp_users)

		with self._mutex:
			self._data.clean()
			self._data.update(tmp_data)
			self._users.clean()
			self._users.update(tmp_users)
		return None
