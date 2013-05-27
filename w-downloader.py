#!/usr/bin/python

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
from datetime import date, datetime, timedelta
import sqlite3
import re

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

def grab_strip_by_number(pattern, number, folder=None):
	return wget(pattern%number, folder)

def grab_strip_by_date(pattern, date, folder=None):
	url = pattern
	for rep in [('%y', str(date.year)),
				('%4y', str(date.year)),
				('%2y', str(date.year)[2:4]),
				('%m', '%02d'%date.month),
				('%d', '%02d'%date.day)]:
		url = url.replace(rep[0], rep[1])
	return wget(url, folder)

def get_filename(url):
	"""Return the name of a file given its URL."""
	return url[1 + url.rfind('/'):]

#
# Date-related control functions
#

def date_get_latest_stored(folder, pattern):
	"""Given the folder to look in and the URL pattern, return the latest stored strip's date."""
	# Determine the pattern the files will be named with
	name_pattern = get_filename(pattern)
	# Build the matcher regex
	name_re = '^'+name_pattern+'$'
	for rep in [('%y', '([0-9]{4})'), ('%4y', '([0-9]{4})'), ('%2y', '([0-9]{2})'), ('%m', '([0-9]{2})'), ('%d', '([0-9]{2})'), ('.', '\\.')]:
		name_re = name_re.replace(rep[0], rep[1])
	# Build the replacer regex
	name_sub = ''
	# TODO: Figure out how to grab values from the sub()ed results
	
	# Get a list of all the files downloaded thus far
	file_list = os.listdir(folder)
	
	# Sort them so the latest ones are first
	file_list.sort(reverse=True)
	
	# Determine the latest file's name
	latest = None
	for f in file_list:
		if None != re.matches(name_re):
			latest = f
			break
	
	if latest = None:
		return None
	else:
		

#
# Numeric-related control functions
#

#
# Date iteration generator
#

def date_iterator(startDate, endDate, delta=timedelta(days=1)):
	currentDate = startDate
	while currentDate < endDate:
		yield currentDate
		currentDate += delta

#
# Database-manipulating functions:
#

db = None

def db_init():
	global db
	db = sqlite3.connect(DATABASE_FILE, isolation_level=None)
	if db == None:
		print('Failed to load database!')
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
# Generally-useful gui functions
#

def label_bold(label):
	if not label.get_use_markup():
		label.set_markup('<b>'+label.get_text()+'</b>')

def label_unbold(label):
	if label.get_use_markup():
		label.set_text(label.get_text())
		label.set_use_markup(False)

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
		
		# Create the radio buttons
		self.radio_numeric = gtk.RadioButton(label='Numeric')
		self.radio_datewise = gtk.RadioButton(group=self.radio_numeric, label='Date-wise')
		
		# Pack the widgets into a grid
		grid = gtk.Table(3, 2, False)
		grid.attach(self.label_name, 0,1, 0,1, xoptions=gtk.FILL, yoptions=gtk.FILL)
		grid.attach(self.label_folder, 0,1, 1,2, xoptions=gtk.FILL, yoptions=gtk.FILL)
		grid.attach(self.label_pattern, 0,1, 2,3, xoptions=gtk.FILL, yoptions=gtk.FILL)
		grid.attach(self.entry_name, 1,2, 0,1, xoptions=gtk.FILL|gtk.EXPAND, yoptions=gtk.FILL)
		grid.attach(self.entry_folder, 1,2, 1,2, xoptions=gtk.FILL|gtk.EXPAND, yoptions=gtk.FILL)
		grid.attach(self.entry_pattern, 1,2, 2,3, xoptions=gtk.FILL|gtk.EXPAND, yoptions=gtk.FILL)
		
		# Pack the radio buttons together
		box = gtk.HBox(homogeneous=True)
		box.pack_start(self.radio_numeric, True, True, 0)
		box.pack_start(self.radio_datewise, True, True, 0)
		
		# Pack the layouts together
		vbox = gtk.VBox()
		vbox.pack_start(grid, True, True, 0)
		vbox.pack_start(box, True, True, 0)
		
		self.get_content_area().add(vbox)
		vbox.show_all()
		
		# Hook up the callbacks
		self.connect('response', self.callback_response)
		self.entry_name.connect('activate', self.callback_trigger, gtk.RESPONSE_ACCEPT)
		self.entry_folder.connect('activate', self.callback_trigger, gtk.RESPONSE_ACCEPT)
		self.entry_pattern.connect('activate', self.callback_trigger, gtk.RESPONSE_ACCEPT)
	
	def callback_response(self, widget, data=None):
		if data == gtk.RESPONSE_ACCEPT:
			# Need to have all fields filled in.
			if not self.check_values():
				return False
		
		elif data == gtk.RESPONSE_REJECT:
			# Clear the dialog
			self.entry_name.set_text('')
			self.entry_folder.set_text('')
			self.entry_pattern.set_text('')
		
		else:
			for label in [self.label_name, self.label_folder, self.label_pattern]:
				label_unbold(label)
			return False
	
	def callback_trigger(self, widget, data=None):
		if self.check_values():
			self.response(gtk.RESPONSE_ACCEPT)
	
	def check_values(self):
		filled = True
		if self.entry_name.get_text() == '':
			filled = False
			label_bold(self.label_name)
		if self.entry_folder.get_text() == '':
			filled = False
			label_bold(self.label_folder)
		if self.entry_pattern.get_text() == '':
			filled = False
			label_bold(self.label_pattern)
		
		if not filled:
			gobject.timeout_add(5000, self.callback_response, 'timeout')
		
		return filled
	
	def run(self):
		result = gtk.Dialog.run(self)
		
		# If the OK button was pressed, put the data into the database
		if result == gtk.RESPONSE_ACCEPT:
			if self.radio_numeric.get_active():
				db_add_webcomic(self.entry_name.get_text(),
								self.entry_folder.get_text(),
								'n: '+self.entry_pattern.get_text())
			else:
				db_add_webcomic(self.entry_name.get_text(),
								self.entry_folder.get_text(),
								'd: '+self.entry_pattern.get_text())
		
		# Do clean-up
		self.hide()
		
		return result
#
# Main Window:
#
class Downloader(gtk.Window):
	def __init__(self):
		gtk.Window.__init__(self)

		# Set window-level stuff
		self.set_title('Webcomic Downloader - v1')
		self.set_geometry_hints(min_width=600, min_height=300)
		self.connect('destroy', gtk.main_quit)

		# Create the toolbar
		self.button_new = gtk.ToolButton(gtk.STOCK_NEW)
		self.button_open = gtk.ToolButton(gtk.STOCK_OPEN)
		self.button_delete = gtk.ToolButton(gtk.STOCK_DELETE)
		
		self.button_new.set_tooltip_text('Add a new Webcomic to the list')
		self.button_open.set_tooltip_text('Download a Webcomic')
		self.button_delete.set_tooltip_text('Delete a Webcomic')

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
		# Show the Add a Webcomic dialog
		if a.run():
			# If the dialog returned True, reload the list
			self.reload_webcomic_list()

	def callback_open(self, widget, data):
		pass

	def callback_delete(self, widget, data):
		(model, pathlist) = self.list_view.get_selection().get_selected_rows()
		for path in pathlist:
			tree_iter = model.get_iter(path)
			print('Deleting webcomic with ID %d'%(model.get_value(tree_iter, 0)))
			#db_delete_webcomic(model.get_value(tree_iter, 0))

db_init()

d = Downloader()
d.show_all()
a = AddWebcomic()

gtk.main()

