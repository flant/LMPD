# -*- coding: utf-8 -*-
#
#       Users filters for LMPD (http://flant.ru/projects/lmpd)
#       UserPolicyLDAP.py
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

import Policy, PySQLPool, subprocess, ldap, traceback, logging

class UserPolicyLDAP(Policy.Policy):
	def __init__(self, config, sql_pool, debug = False):
		Policy.Policy.__init__(self, config, sql_pool, debug)

		self._alias_maps  = self._postconf()

		self._ldap_uri = config.get("filters_UserPolicyLDAP_ldap_addr", "ldaps://127.0.0.1")

		self._ldap_user = config.get("filters_UserPolicyLDAP_ldap_user", "cn=mail,ou=main,dc=acmeinc,dc=en")
		self._ldap_pass = config.get("filters_UserPolicyLDAP_ldap_pass", "")
		self._ldap_base_dn = config.get("filters_UserPolicyLDAP_ldap_base_dn", "dc=acmeinc,dc=en")
		self._ldap_mail_attr = config.get("filters_UserPolicyLDAP_ldap_mail_attr", "mail")
		self._ldap_id_attr = config.get("filters_UserPolicyLDAP_ldap_id_attr", "id")
		self._ldap_search_filter = config.get("filters_UserPolicyLDAP_ldap_search_filter", "(&(objectClass=Account)(mail=*))")
		self._keep_rules = config.get("filters_keep", True)
		self._exclude_mails = config.get("filters_exclude", list())

		self._mail_users, self._uid_users = self._loadldap()

		if self._mail_users:
			tmp_data = self._loadsql(self._mail_users)
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

		if self._data.has_key(recipient) and self._data[recipient].has_key(sender):
			result = self._data[recipient][sender]

		return result

	def _postalias(self, recipient, deep = 1):

		if (deep > 50):
			return recipient
		try:
			post_alias = subprocess.Popen(["postalias -q {0} {1}".format(recipient, self._alias_maps )], shell = True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=None)
		except:
			logging.warn("Error in getting alias data for UserLdap policy. Traceback: \n{0}\n".format(traceback.format_exc()))
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
			logging.error("Error in getting postconf data for UserLdap policy. Traceback: \n{0}\n".format(traceback.format_exc()))
			raise BaseException('Postconf error')

		conf = post_conf.communicate()[0].strip().replace("\n", " ").replace(",", "")
		return conf

	def train(self, data, answer = "dspam_innocent"):
		return self._train_one(data , answer)

	def _train_one(self, data, answer = "dspam_innocent"):
		recipient = data["recipient"]
		sender = data["sender"]

		if self._debug:
			logging.debug("Start training for user {0} with mail {1}".format(sender, recipient))

		if sender in self._exclude_mails:
			return None

		if recipient != "" and sender != "":
			if not self._data.has_key(sender): self._data[sender] = {}
			if not self._data[sender].has_key(recipient):
				if self._addrule(data, answer):
					self._data[sender][recipient] = answer

		return None

	def _del_one(self, data):

		recipient = data["recipient"]
		sender = data["sender"]

		if self._debug:
			logging.debug("Start training for user {1} with mail {0}".format(sender, recipient))

		if recipient != "" and sender != "":
			if not self._data.has_key(sender): self._data[sender] = {}
			if self._data[sender].has_key(recipient):
				if self._delrule(data):
					del self._data[sender][recipient]

		return None

	def _loadsql(self, users):
		try:
			sql_1 = "SELECT `user_id`, `mail`, `accept` FROM `white_list_mail`"
			sql_2 = "DELETE FROM `white_list_mail` WHERE `user_id` = '{0}'"

			res={}
			rules={}
			clean_rules=list()

			for uid in users:
				if users[uid] in self._exclude_mails:
					continue
				res[users[uid]] = {}

			query = PySQLPool.getNewQuery(self._sql_pool, True)

			query.Query(sql_1)
			for row in query.record:
				tmp = {}
				tmp[row["mail"].lower()] = row["accept"]
				if users.has_key(str(int(row["user_id"]))):
					res[users[str(int(row["user_id"]))]].update(tmp)
				else:
					if not self._keep_rules:
						clean_rules.append(row["user_id"])
						
			if not self._keep_rules:
				clean_rules = list(set(clean_rulse))
				for id in clean_rulse:
					query.Query(sql_2.format(id))
			return res
		except:
			if self._debug:
				logging.debug("Error in getting SQL data for UserLdap policy. Traceback: \n{0}\n".format(traceback.format_exc()))
			return None

	def _loadldap(self):
		result_mail_set = {}
		result_uid_set = {}
		try:
			ldap_conn = ldap.open(self._ldap_uri)
			ldap_conn.protocol_version = ldap.VERSION3
			ldap_conn.simple_bind_s(self._ldap_user, self._ldap_pass)
		except:
			if self._debug:
				logging.debug("Error in creating LDAP connection for UserLdap policy. Traceback: \n{0}\n".format(traceback.format_exc()))
			return None, None

		try:
			ldap_result_id = ldap_conn.search(self._ldap_base_dn, ldap.SCOPE_SUBTREE, self._ldap_search_filter, [self._ldap_mail_attr,self._ldap_id_attr])
			while (True):
				result_type, result_data = ldap_conn.result(ldap_result_id, 0)
				if (result_data == []):
					break
				else:
					if result_type == ldap.RES_SEARCH_ENTRY:
						result_mail_set[result_data[0][1][self._ldap_id_attr][0]] = result_data[0][1][self._ldap_mail_attr][0].lower()
						result_uid_set[result_data[0][1][self._ldap_mail_attr][0].lower()] = result_data[0][1][self._ldap_id_attr][0]
		except:
			if self._debug:
				logging.debug("Error in getting LDAP data for UserLdap policy. Traceback: \n{0}\n".format(traceback.format_exc()))
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
					if self._debug:
						logging.debug("Adding SQL request: " + sql_1.format(tmp, data["recipient"], answer))
					query.Query(sql_1.format(tmp, data["recipient"], answer))
					return True
				else:
					return False
			except:
				logging.warn("Error in creating a rule for UserLdap policy. Traceback: \n{0}\n".format(traceback.format_exc()))
				return False

	def _delrule(self, data):
		sql_1 = "DELETE FROM `white_list_mail` WHERE `user_id` = '{0}' AND `mail` = '{1}'"

		if data["sasl_username"] != "" and data["sender"] != "" and data["recipient"] != "":
			try:
				query = PySQLPool.getNewQuery(self._sql_pool, True)

				if self._uid_users.has_key(data["sasl_username"]):
					tmp = self._uid_users[data["sasl_username"]]
					if self._debug:
						logging.debug("Deleting SQL request: " + sql_1.format(tmp, data["recipient"]))
					query.Query(sql_1.format(tmp, data["recipient"]))
					return True
				else:
					return False
			except:
				logging.warn("Error in deleting a rule for UserLdap policy. Traceback: \n{0}\n".format(traceback.format_exc()))
				return False

	def reload(self):

		tmp_users, tmp_uids = self._loadldap()
		if tmp_users:
			tmp_data = self._loadsql(tmp_users)
		else:
			tmp_data = {}

		if tmp_data and tmp_uids:
			self._data.clear()
			self._data.update(tmp_data)
			self._mail_users.clear()
			self._mail_users.update(tmp_users)
			self._uid_users.clear()
			self._uid_users.update(tmp_uids)

		return None
