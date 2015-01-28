#!/usr/bin/python3

#
# Webcomic downloading tool, version 2
# Uses Python 3 and GTK3
#

import os
import time
from datetime import date, datetime, timedelta
import sqlite3
import re
import traceback

from gi.repository import Gtk
from gi.repository import GObject

DATABASE_FILE = '.webcomic-list-v2.sqlite3'

TODO = """
Stuff to do: (in rough order)
	Cheap out on main window to begin with.
		Just something functional enough to work on everything else.
	Add way to add a webcomic.
		Multi-step process:
			1: Ask for URL.
			2: Show user the page, can grab the webcomic's title from the page.
			3: Get the user to point out the "Next" and "Previous" links.
			4: Get the user to point out where the image(s) for the comic is/are.
			5: Have user specify whether to rename the webcomic images or not.
			6: Start download process.
	Add way to pause and/or stop the download process.
	Add way to resume and/or continue downloading images.

Things that need to be stored about each webcomic:
	ID (int)
	Name (str)
	Description? (str)
	Folder (str)
	Date added (str)
	Latest comic page URL (str)
	URL of last comic downloaded (str)
	Date of last comic downloaded (str)
	
	List of strings detailing how to navigate between pages,
		where the comic images are,
		and how the images should be named when saved.

Stuff to eventually do:
	Add support for recalibrating how each item needed is found.
		(ie, next, previous, comic images, etc)
	Add support for moving folders.
"""

class MainWindow:
	def __init__(self):
		# Prepare main window
		self.window = Gtk.Window('Webcomic Downloader - v2')
		self.window.set_size_request(600, 300)
		self.connect('destroy', gtk.main_quit)
		
		# Create the toolbar
		self.button_new = Gtk.ToolButton(gtk.STOCK_NEW)
		
		self.button_new.set_tooltip_text('Add a new webcomic')
		
		self.button_new.connect('clicked', self.callback_new, 'new')
		
		self.toolbar = Gtk.Toolbar()
		self.toolbar.insert(self.button_new)
		
		box = Gtk.VBox(False, 5)
		box.pack_start(self.toolbar, False, True, 0)
		
		self.window.get_content_area().pack_start(box, True, True, 0)
		
		# Create the empty list-view
		self.list_data = Gtk.ListStore(int, # ID
									   str, # Name
									   str, # Folder
									   str, # Date added
									   str, # URL of current comic
									   str, # URL of the last comic downloaded
									   str, # Date of last comic downloaded
									   )
		
		renderer = Gtk.CellRendererText()
		self.tree_view = Gtk.TreeView(self.list_data)
		self.tree_view.get_selection().set_mode(Gtk.SelectionMode.SINGLE)
		c = Gtk.TreeViewColumn('Name', renderer, text=1)
		c.set_expand(True)
		c.set_resizable(True)
		self.tree_view.append_column(c)
		c = Gtk.TreeViewColumn('Folder', renderer, text=2)
		c.set_resizable(True)
		self.tree_view.append_column(c)
		