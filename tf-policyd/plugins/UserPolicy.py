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

def loadsql(SqlPool):
	Sql_1 = "SELECT `id`,`username` FROM `users`"
	Sql_2 = "SELECT `user_id`, `mail`, `accept` FROM `white_list_mail`"

	Res={}
	Users={}
	Rules={}
	query = PySQLPool.getNewQuery(SqlPool, True)
	query.Query(Sql_1)
	for row in query.record:
		Tmp = row["username"].lower()
		Users[str(int(row["id"]))] = Tmp
		Res[Tmp] = {}

	query.Query(Sql_2)
	for row in query.record:
		Tmp = {}
		Tmp[row["mail"].lower()] = row["accept"]
		Res[Users[str(int(row["user_id"]))]].update(Tmp)

	return Res

def addrule(Data, SqlPool, Answer = "dspam_innocent"):
	if Data["sasl_username"] != "" and Data["sender"] != "" and Data["recipient"] != "":

		Sql_1 = "SELECT `id` FROM `users` WHERE `username` LIKE '{0}'"
		Sql_2 = "INSERT IGNORE INTO `white_list_mail` VALUES(NULL, {0}, '{1}', '{2}')"

		query = PySQLPool.getNewQuery(SqlPool, True)
		query.Query(Sql_1.format(Data["sasl_username"]))
		try:
			Tmp = str(int(query.record[0]["id"]))
		except IndexError as Err:
			return None

		query.Query(Sql_2.format(Tmp, Data["recipient"], Answer))

def delrule(Data, SqlPool):
	Sql_1 = "SELECT `id` FROM `users` WHERE `username` LIKE '{0}'"
	Sql_2 = "DELETE FROM `white_list_mail` WHERE `user_id` = '{0}' AND `mail` = '{1}'"

	if Data["sender"] != "" and Data["recipient"] != "":
		query = PySQLPool.getNewQuery(SqlPool, True)
		query.Query(Sql_1.format(Data["sender"]))
		try:
			Tmp = str(int(query.record[0]["id"]))
		except IndexError as Err:
			return None

		query.Query(Sql_2.format(Tmp, Data["recipient"]))

class UserPolicy(Policy.Policy):
	def __init__(self, Data, SqlPool):
		self.mutex = threading.Lock()
		Policy.Policy.__init__(self, Data, SqlPool)
		self.ConfAliases = self._postconf()

	def check(self, Data):
		if Data["request"] == "smtpd_access_policy":
			if Data["sasl_username"] == "":
				Sender = Data["sender"]
				Recipient = self._postalias(Data["recipient"])
				Answer = self._strict_check(Data["recipient"], Sender)
				if Answer:
					return Answer
				else:
					if Recipient:
						Recipient = list(set(aRecipient))
						for Email in Recipient:
							Answer = self._strict_check(Email.lower(), Sender)
							if Answer: break

						if Answer:
							return Answer
						else:
							return None
					else:
						return None
			else:
				self.train(Data)
				return None
		elif Data["request"] == "junk_policy":

			if Data["action"] == "notspam":
				if not self._strict_check(Data["sender"], Data["recipient"]):
					self._strict_train(Data)

			elif Data["action"] == "spam":
				if self._strict_check(Data["sender"], Data["recipient"]):
					self._strict_del(Data)
			else:
				return None
		else:
			return None

	def _strict_check(self, Recipient, Sender):
		if self.Data.has_key(Recipient) and self.Data[Recipient].has_key(Sender):
			return self.Data[Recipient][Sender]
		else:
			return None

	def _postalias(self, Recipient):
		PostAlias = subprocess.Popen(["postalias -q {0} {1}".format(Recipient, self.ConfAliases)], shell = True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=None)
		Output = PostAlias.communicate()[0].strip().lower()
	        Res = list()
		if Output == Recipient.lower().strip() or PostAlias.returncode:
			return None
		else:
			TestMails = Output.split(",")
			for Email in TestMails:
				Answer = self._postalias(Email.strip())
				if Answer:
					Res += aAnswer
				else:
					if not Email in Res:
						Res.append(Email.strip())

		return Res

	def _postconf(self):
		PostConf = subprocess.Popen(["postconf -h virtual_alias_maps alias_maps"], shell = True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=None)
		Conf = PostConf.communicate()[0].strip().replace("\n", " ").replace(",", "")
		return Conf

	def train(self, Data, Answer = "dspam_innocent"):
		Tmp = self._strict_train(Data , Answer)
		return Tmp

	def _strict_train(self, Data, Answer = "dspam_innocent"):
		print Data
		Recipient = Data["recipient"]
		Sender = Data["sender"]

		with self.mutex:
			if Recipient != "" and Sender != "":
				if not self.Data.has_key(Sender): self.Data[Sender] = {}
				
				if not self.Data[Sender].has_key(Recipient):

					addrule(Data, self.SqlPool, Answer)
					self.Data[Sender][Recipient] = Answer

		return None

	def _strict_del(self, Data):

		Recipient = Data["recipient"]
		Sender = Data["sender"]

		with self.mutex:
			if Recipient != "" and Sender != "":

				if not self.Data.has_key(Sender): self.Data[Sender] = {}
				if self.Data[Sender].has_key(Recipient):

					delrule(Data, self.SqlPool)
					del self.Data[Sender][Recipient]
		return None
