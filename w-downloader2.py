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


#
# Comic-grabbing functions:
#

def wget(url, folder=None):
	"""wget(url, folder=None)
	Given the URL (and optionally, the folder to put it in), download the given URL.
	Returns True if the operation was successful, False otherwise."""
	if folder == None:
		result = os.system('wget "%s"'%url)
	else:
		result = os.system('wget -P "%s" "%s"'%(folder, url))
	return (result==0)

#
# Comic-page manipulating functions:
#

def page_get_next(html):
	"""Given the BeautifulSoup source of a page, return the URL for the next one, or None if it can't be determined."""
	# First, try asking for the <link rel="next"> tag
	result = html.findAll('link', rel='next')
	if len(result) > 0:
		return result[0].get('href')
	
	# Next, try looking for an array of <img> tags that use any of a number of ALT or TITLE attributes
	

def matches_next(tag):
	MATCHERS = [re.compile(a, re.IGNORECASE) for a in ['next', 'tomorrow']]
	# If it's an <A> tag with a string as its only child:
	if tag.name == 'a' and tag.string != None:
		for m in MATCHERS:
			if m.match(tag.string) != None:
				return tag.get('href')
	
	# Look for an <IMG> tag's TITLE attribute
	for m in MATCHERS:
		for t in tag.findAll('img', title=m)
			return tag.get('href')
		for t in tag.findAll('img', alt=m)
			return tag.get('href')
	
	return None

#
# Download-control function:
#

def strip_downloader(folder):
	pass
