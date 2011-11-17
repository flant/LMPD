# -*- coding: utf-8 -*-
#
#       Base filter class for lmpd
#       Policy.py
#       
#       Copyright (C) 2009-2011 CJSC Flant (www.flant.ru)
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

import threading

class Policy():
	def __init__(self, config, sql_pool):
		self._mutex = threading.Lock()

	def train(self, data):
		return None

	def check(self, data):
		return None
		
	def reload(self):
		return None
