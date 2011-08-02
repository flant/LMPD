# -*- coding: utf-8 -*-
#
#		Config for policyd
#       AnalysePolicy.py
#       
#       Copyright (C) 2009-2011 CJSC TrueOffice (www.trueoffice.ru)
#		Written by Dmitry Stolyarov <dmitry.stolyarov@trueoffice.ru>
#		Modified by Nikolay aka GyRT Bogdanov <nikolay.bogdanov@@trueoffice.ru>
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

import yaml, argparse, os, sys

class ConfigError(Exception):
	def __init__(self, value):
		self.value = value

	def __str__(self):
		return 'No such key: ' + self.value

class Config(dict):
	def __init__(self):
		dict.__init__(self)
		Parser = argparse.ArgumentParser(description='Mini whitelisting daemon.')
		Parser.add_argument('-c', '--config', help='Path to a config file', default='/etc/postfix/policyd.yaml')
		Parser.add_argument('-p', '--pid', help='Path to a PID file', default='/var/run/policyd.pid')
		Parser.add_argument('-d', dest='bDaemon', action='store_true', help='Become a daemon', default=False)
		Args = Parser.parse_args()
		self["argv"] = {}
		self["argv"]["config"] = Args.config
		self["argv"]["pid"] = Args.pid
		self["argv"]["daemon"] = Args.bDaemon
		if os.path.exists(self["argv"]["config"]):
			with file(self["argv"]["config"], 'r') as stream:
				self.update(yaml.load(stream))
				stream.close
		else:
			print "Cound not find config file. Exiting..."
			sys.exit(1)

	def _split_key(self, key):
		key_seq = key.split('_')
		return key_seq[0], key_seq[1:]

	def _try_next_key(self, first_key, key_seq):
		return first_key + '_' + key_seq[0], key_seq[1:]

	def _find(self, node, key):
		first_key, key_seq = self._split_key(key)

		while True:
			if first_key in node:
				if len(key_seq):
					try:
						return self._find(node[first_key], '_'.join(key_seq))
					except: pass
				else:
					return node[first_key]			
			if not len(key_seq):
				raise ConfigError(key)
			else:
				first_key, key_seq = self._try_next_key(first_key, key_seq)

	def get(self, key = '', default = None):
		if not len(key): return self
		try:
			return self._find(self, key)
		except:
			if default != None: return default
			raise

	def get_any(self, key_seq, default = None):
		try:
			return self.get(key_seq[0])
		except:
			if len(key_seq) > 1:
				return self.get_any(key_seq[1:])
			elif default != None:
				return default
			raise
