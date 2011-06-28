#
# Copyright (C) 2009-2011 CJSC TrueOffice (www.trueoffice.ru)
# Written by Dmitry Stolyarov <dmitry.stolyarov@trueoffice.ru>
# Modified by Nikolay Bogdanov <nikolay.bogdanov@@trueoffice.ru>
#

# -*- coding: utf-8 -*-

import yaml, argparse, os, sys

class ConfigError(Exception):
	def __init__(self, value):
		self.value = value

	def __str__(self):
		return 'No such key: ' + self.value

class Config(dict):
	def __init__(self):
		dict.__init__(self)
		oParser = argparse.ArgumentParser(description='Mini whitelisting daemon.')
		oParser.add_argument('-c', '--config', help='Path to a config file', default='/etc/postfix/policyd.yaml')
		oParser.add_argument('-p', '--pid', help='Path to a PID file', default='/var/run/policyd.pid')
		oParser.add_argument('-d', dest='bDaemon', action='store_true', help='Become a daemon', default=False)
		oArgs = oParser.parse_args()
		self["argv"] = {}
		self["argv"]["config"] = oArgs.config
		self["argv"]["pid"] = oArgs.pid
		self["argv"]["daemon"] = oArgs.bDaemon
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
