#!/usr/bin/python3

#
# Webcomic downloading tool
#

import pygtk
pygtk.require('2.0')
import gtk
import gobject
import pango

import os
import time
import sqlite3

DATABASE_FILE = '.webcomic-list.sqlite3'

#
# The database table specifications
#
sql_webcomics = """
CREATE TABLE IF NOT EXISTS Webcomics (
	id INTEGER PRIMARY KEY,
	name TEXT NOT NULL,
	folder TEXT NOT NULL,
	pattern TEXT NOT NULL,
	date_added TEXT DEFAULT (CURRENT_TIMESTAMP)
);
"""

#
# Comic-grabbing functions:
#

def wget(url, folder=None):
	if folder == None:
		result = os.system('wget "%s"'%url)
	else:
		result = os.system('wget -P "%s" "%s"'%(folder, url))
	return (result==0)

def grab_strip(pattern, number, folder=None):
	return wget(pattern%number, folder)

#
# Database-manipulating functions:
#

db = None

def db_init():
	global db
	db = sqlite3.connect(DATABASE_FILE, isolation_level=None)
	if db == None:
		print 'Failed to load database!'
		exit(1)
	cursor = db.cursor()
	cursor.execute("SELECT tbl_name FROM sqlite_master WHERE type='table' ORDER BY tbl_name;")
	tables = cursor.fetchall()
	tables = [ t[0] for t in tables]
	if 'Webcomics' not in tables:
		cursor.execute(sql_webcomics)

def db_count_webcomics():
	global db
	cursor = db.cursor()
	cursor.execute('SELECT COUNT(id) FROM Webcomics;')
	return cursor.fetchone()[0]

def db_add_webcomic(name, folder, pattern):
	global db
	cursor = db.cursor()
	cursor.execute('INSERT INTO Webcomics (name, folder, pattern) VALUES ("%s", "%s", "%s");'%(name, folder, pattern))
	return cursor.lastrowid

def db_delete_webcomic(webcomic_id):
	global db
	cursor = db.cursor()
	cursor.execute('DELETE FROM Webcomics WHERE id=%d;'%webcomic_id)

def db_list_webcomics():
	global db
	cursor = db.cursor()
	cursor.execute('SELECT id, name, folder, pattern, date_added FROM Webcomics ORDER BY id;')
	return cursor.fetchall()

#
# Add a webcomic dialog:
#

class AddWebcomic(gtk.Dialog):
	def __init__(self, parent=None):
		gtk.Dialog.__init__(self, 'Webcomic Downloader - Add a webcomic',
					parent, gtk.DIALOG_MODAL|gtk.DIALOG_DESTROY_WITH_PARENT,
					('_Save', gtk.RESPONSE_ACCEPT, '_Cancel', gtk.RESPONSE_REJECT))
		
		# Set dialog-level stuff
		self.set_default_response(gtk.RESPONSE_ACCEPT)
		
		# Create the Entry widgets
		self.entry_name = gtk.Entry()
		self.entry_folder = gtk.Entry()
		self.entry_pattern = gtk.Entry()
		
		# Create the Labels
		self.label_name = gtk.Label('The webcomic\'s name:')
		self.label_folder = gtk.Label('Folder name to put the comics in:')
		self.label_pattern = gtk.Label('URL Pattern of the webcomic\'s images:')
		
		# Prepare for alternate styles:
		for label in [self.label_name, self.label_folder, self.label_pattern]:
			label.set_markup('<b>'+label.get_text()+'</b>')
			label.set_use_markup(False)
		
		# Pack the widgets into a grid
		grid = gtk.Table(3, 2, False)
		grid.attach(self.label_name, 0,1, 0,1, xoptions=gtk.FILL, yoptions=gtk.FILL)
		grid.attach(self.label_folder, 0,1, 1,2, xoptions=gtk.FILL, yoptions=gtk.FILL)
		grid.attach(self.label_pattern, 0,1, 2,3, xoptions=gtk.FILL, yoptions=gtk.FILL)
		grid.attach(self.entry_name, 1,2, 0,1, xoptions=gtk.FILL|gtk.EXPAND, yoptions=gtk.FILL)
		grid.attach(self.entry_folder, 1,2, 1,2, xoptions=gtk.FILL|gtk.EXPAND, yoptions=gtk.FILL)
		grid.attach(self.entry_pattern, 1,2, 2,3, xoptions=gtk.FILL|gtk.EXPAND, yoptions=gtk.FILL)
		
		self.get_content_area().add(grid)
		grid.show_all()
		
		# Hook up the callbacks
		self.connect('response', self.callback_response)
		self.entry_name.connect('activate', self.callback_response, gtk.RESPONSE_ACCEPT)
		self.entry_folder.connect('activate', self.callback_response, gtk.RESPONSE_ACCEPT)
		self.entry_pattern.connect('activate', self.callback_response, gtk.RESPONSE_ACCEPT)
	
	def callback_response(self, widget, data=None):
		if data == gtk.RESPONSE_ACCEPT:
			# TODO: Make sure there's data where it needs to be.
			# Need to have all fields filled in.
			filled = True
			if self.entry_name.get_text() == '':
				filled = False
				self.label_name.set_use_markup(True)
			if self.entry_folder.get_text() == '':
				filled = False
				self.label_folder.set_use_markup(True)
			if self.entry_pattern.get_text() == '':
				filled = False
				self.label_pattern.set_use_markup(True)
			
			if filled:
				# Allow this signal to propogate further
				pass
			else:
				# Stop us from going further
				gobject.timeout_add(2000, self.callback_response, 'timeout')
				return False
		
		elif data == gtk.RESPONSE_REJECT:
			# Clear the dialog
			self.entry_name.set_text('')
			self.entry_folder.set_text('')
			self.entry_pattern.set_text('')
		
		else:
			for label in [self.label_name, self.label_folder, self.label_pattern]:
				label.set_use_markup(False)
			return False
	
	
	def run(self):
		gtk.Dialog.run(self)
		
		# Do clean-up
		self.hide()
#
# Main Window:
#
class Downloader(gtk.Window):
	def __init__(self):
		gtk.Window.__init__(self)

		# Set window-level stuff
		self.set_title('Webcomic Downloader - v1')
		self.set_geometry_hints(min_width=300, min_height=300)
		self.connect('destroy', gtk.main_quit)

		# Create the toolbar
		self.button_new = gtk.ToolButton(gtk.STOCK_NEW)
		self.button_open = gtk.ToolButton(gtk.STOCK_OPEN)
		self.button_delete = gtk.ToolButton(gtk.STOCK_DELETE)

		self.button_new.connect('clicked', self.callback_new, 'new')
		self.button_open.connect('clicked', self.callback_open, 'open')
		self.button_delete.connect('clicked', self.callback_delete, 'delete')

		self.toolbar = gtk.Toolbar()
		self.toolbar.insert(self.button_new, -1)
		self.toolbar.insert(self.button_open, -1)
		self.toolbar.insert(self.button_delete, -1)

		box = gtk.VBox(False, 5)
		box.pack_start(self.toolbar, False, True, 0)

		self.add(box)

		# Create the (empty) grid-box
		self.list_data = gtk.ListStore(gobject.TYPE_INT64, # ID
										gobject.TYPE_STRING, # Name
										gobject.TYPE_STRING, # Folder
										gobject.TYPE_STRING, # Pattern
										gobject.TYPE_STRING) # Date added

		self.cell_renderer = gtk.CellRendererText()
		self.list_view = gtk.TreeView(self.list_data)
		self.list_view.insert_column_with_attributes(-1, 'Name', self.cell_renderer, text=1)
		self.list_view.insert_column_with_attributes(-1, 'Folder', self.cell_renderer, text=2)
		self.list_view.insert_column_with_attributes(-1, 'Pattern', self.cell_renderer, text=3)

		for column in self.list_view.get_columns():
			column.set_resizable(True)

		self.list_scroller = gtk.ScrolledWindow()
		self.list_scroller.add(self.list_view)
		self.list_scroller.set_shadow_type(gtk.SHADOW_IN)
		self.list_scroller.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_ALWAYS)

		box.pack_start(self.list_scroller, True, True, 0)

		self.reload_webcomic_list()

	def reload_webcomic_list(self):
		# Load the list of webcomics into the list
		webcomics = db_list_webcomics()
		for comic in webcomics:
			self.list_data.append(comic)

	def callback_new(self, widget, data):
		# TODO: Show the Add a Webcomic dialog
		# TODO: If the dialog returned True, reload the list
		a.run()
		pass

	def callback_open(self, widget, data):
		pass

	def callback_delete(self, widget, data):
		pass

db_init()

d = Downloader()
d.show_all()
a = AddWebcomic()

gtk.main()

