#!/usr/bin/python

#
# Webcomic downloading tool, V2
#


import pygtk
pygtk.require('2.0')
import gtk
import gobject
import pango

import os
import time
from datetime import date, datetime, timedelta
import sqlite3
import re
import traceback

import urllib2
from bs4 import BeautifulSoup

import collector

DATABASE_FILE = '.w-downloader2.sqlite3'

TODO = """
Stuff to do:
	Finish the table declaration.
	Create the main window.
	Create the Add Webcomic dialog.
	Add the functions for finding the Next and Previous links.
	Complete the function that downloads the webcomic's images.
	? Convert the webcomic-managing code into a module?
"""

#
# The database table specifications
#
sql_webcomics = """
CREATE TABLE IF NOT EXISTS Webcomics (
	id INTEGER PRIMARY KEY,
	name TEXT NOT NULL,
	folder TEXT NOT NULL,
	date_added TEXT DEFAULT (CURRENT_TIMESTAMP),
	last_page TEXT NOT NULL,
	todays_page TEXT NULL,
	
);"""

class AddWebcomic(gtk.Dialog):
	def __init__(self, parent=None):
		gtk.Dialog.__init__(self, 'Webcomic Downloader v2 - Add a webcomic',
							parent, gtk.DIALOG_MODAL|gtk.DIALOG_DESTROY_WITH_PARENT,
							('_Save', gtk.RESPONSE_ACCEPT, '_Cancel', gtk.RESPONSE_REJECT))
		
		self.set_default_response(gtk.RESPONSE_ACCEPT)
		
		# TODO: Complete the Add Webcomic dialog

class MainWindow(gtk.Window):
	def __init__(self):
		gtk.Window.__init__(self)
		
		# TODO: Complete the Main Window

mw = MainWindow()
aw = AddWebcomic(mw)
dw = DownloadWebcomic(mw)

gtk.main()

