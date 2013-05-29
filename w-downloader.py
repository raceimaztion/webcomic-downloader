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
import traceback

DATABASE_FILE = '.webcomic-list.sqlite3'
ALL_IMAGE_TYPES = ['.gif', '.png', '.jpg']

TODO = """
TODO:
	Allow some method for duplicating and/or editing a Webcomic's info.
	Complete support for date-wise image naming.
	Add support for stopping the downloader.
"""

#
# The database table specifications
#
sql_webcomics = """
CREATE TABLE IF NOT EXISTS Webcomics (
	id INTEGER PRIMARY KEY,
	name TEXT NOT NULL,
	folder TEXT NOT NULL,
	pattern TEXT NOT NULL,
	date_added TEXT DEFAULT (CURRENT_TIMESTAMP),
	skipsafe INTEGER DEFAULT (5)
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
	return (wget(pattern%number, folder), get_filename(pattern%number))

def grab_strip_by_date(pattern, date, folder=None):
	url = pattern
	for rep in [('%y', str(date.year)),
				('%4y', str(date.year)),
				('%2y', str(date.year)[2:4]),
				('%m', '%02d'%date.month),
				('%d', '%02d'%date.day)]:
		url = url.replace(rep[0], rep[1])
	return (wget(url, folder), get_filename(url))

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
	
	if latest == None:
		print('Found no matching webcomic images!')
		return False
	else:
		# TODO: Parse the filename into a date object
		pass

#
# Numeric-related control functions
#

def numeric_get_latest_stored(folder, pattern, check_all_formats=False):
	"""Given the folder to look in and the URL pattern, return the latest stored strip's number."""
	name_pattern = get_filename(pattern)
	name_re = '^' + re.sub('%([0-9])+d', '([0-9]{\g<1>,})', name_pattern.replace('%d', '([0-9]+)').replace('.', '\\.'))
	name_re = re.sub('{0+', '{', name_re)
	
	if check_all_formats:
		print('checking all formats.')
		name_re += '\\'
	else:
		print('Only one format to check.')
		name_re += '$'
	
	# Debugging:
	print('name pattern: '+name_pattern)
	print('name_re: '+name_re)
	
	file_list = os.listdir(folder)
	file_list.sort(reverse=True)
	
	latest = None
	for f in file_list:
		if check_all_formats:
			for format in ALL_IMAGE_TYPES:
				if None != re.match(name_re + format + '$', f):
					latest = f
					break
			if latest != None:
				break
		else:
			if None != re.match(name_re, f):
				latest = f
				break
	
	if latest == None:
		print 'Found no matching webcomic images!'
		return False
	else:
		if check_all_formats:
			return int(re.sub(name_re + '..*', '\g<1>', latest), 10)
		else:
			return int(re.sub(name_re, '\g<1>', latest), 10)

def numeric_download(name, folder, pattern, skipsafe, check_all=False):
	"""Given the Webcomic data, grab the webcomic images sequentially.
		Yields after each download attempt returning (was_success, strip_number) for each."""
	last = numeric_get_latest_stored(folder, pattern, check_all)
	if last == False:
		yield (None, 'Failed to find any strips matching the given pattern!')
		return
	
	print('Downloading strip images for %s.'%name)
	print('Last downloaded strip was #%d.'%last)
	
	yield (None, last, get_filename(pattern%last))
	
	#test="""
	number = last + 1
	filename = ''
	
	while skipsafe > 0:
		if check_all:
			for format in ALL_IMAGE_TYPES:
				result = grab_strip_by_number(pattern + format, number, folder)
				if result[0]:
					filename = result[1]
					break
				else:
					time.sleep(0.5)
		else:
			result = grab_strip_by_number(pattern, number, folder)
			filename = result[1]
		if not result[0]:
			skipsafe -= 1
		yield (result[0], number, filename)
		number += 1
	#"""

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

def db_add_webcomic(name, folder, pattern, skipsafe=None):
	global db
	cursor = db.cursor()
	if skipsafe != None and type(skipsafe) == int:
		cursor.execute('INSERT INTO Webcomics (name, folder, pattern, skipsafe) VALUES ("%s", "%s", "%s", %d);'%(name, folder, pattern, skipsafe))
	else:
		cursor.execute('INSERT INTO Webcomics (name, folder, pattern) VALUES ("%s", "%s", "%s");'%(name, folder, pattern))
	return cursor.lastrowid

def db_delete_webcomic(webcomic_id):
	global db
	cursor = db.cursor()
	cursor.execute('DELETE FROM Webcomics WHERE id=%d;'%webcomic_id)

def db_list_webcomics():
	global db
	cursor = db.cursor()
	cursor.execute('SELECT id, name, folder, pattern, date_added, skipsafe FROM Webcomics ORDER BY id;')
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
		self.spin_skipsafe = gtk.SpinButton(gtk.Adjustment(value=3, lower=0, upper=10, step_incr=1))
		self.check_all_types = gtk.CheckButton(label='.gif, .png, .jpg')
		
		# Create the Labels
		self.label_name = gtk.Label('The webcomic\'s name:')
		self.label_folder = gtk.Label('Folder name to put the comics in:')
		self.label_pattern = gtk.Label('URL Pattern of the webcomic\'s images:')
		self.label_skipsafe = gtk.Label('Number of missed strips before stopping:')
		self.label_check_all = gtk.Label('Webcomic uses a variety of image types:')
		
		# Create the radio buttons
		self.radio_numeric = gtk.RadioButton(label='Numeric')
		self.radio_datewise = gtk.RadioButton(group=self.radio_numeric, label='Date-wise')
		
		# Pack the widgets into a grid
		grid = gtk.Table(5, 2, False)
		grid.attach(self.label_name, 0,1, 0,1, xoptions=gtk.FILL, yoptions=gtk.FILL)
		grid.attach(self.label_folder, 0,1, 1,2, xoptions=gtk.FILL, yoptions=gtk.FILL)
		grid.attach(self.label_pattern, 0,1, 2,3, xoptions=gtk.FILL, yoptions=gtk.FILL)
		grid.attach(self.label_skipsafe, 0,1, 3,4, xoptions=gtk.FILL, yoptions=gtk.FILL)
		grid.attach(self.label_check_all, 0,1, 4,5, xoptions=gtk.FILL, yoptions=gtk.FILL)
		grid.attach(self.entry_name, 1,2, 0,1, xoptions=gtk.FILL|gtk.EXPAND, yoptions=gtk.FILL)
		grid.attach(self.entry_folder, 1,2, 1,2, xoptions=gtk.FILL|gtk.EXPAND, yoptions=gtk.FILL)
		grid.attach(self.entry_pattern, 1,2, 2,3, xoptions=gtk.FILL|gtk.EXPAND, yoptions=gtk.FILL)
		grid.attach(self.spin_skipsafe, 1,2, 3,4, xoptions=gtk.FILL|gtk.EXPAND, yoptions=gtk.FILL)
		grid.attach(self.check_all_types, 1,2, 4,5, xoptions=gtk.FILL|gtk.EXPAND, yoptions=gtk.FILL)
		
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
		# Clear the dialog
		self.entry_name.set_text('')
		self.entry_folder.set_text('')
		self.entry_pattern.set_text('')
		self.spin_skipsafe.set_value(3)
		self.check_all_types.set_active(False)
		
		result = gtk.Dialog.run(self)
		
		# If the OK button was pressed, put the data into the database
		if result == gtk.RESPONSE_ACCEPT:
			prefix = ''
			if self.radio_numeric.get_active():
				if self.check_all_types.get_active():
					prefix = 'na:'
				else:
					prefix = 'n: '
			else:
				if self.check_all_types.get_active():
					prefix = 'pa:'
				else:
					prefix = 'p: '
			
			db_add_webcomic(self.entry_name.get_text(),
							self.entry_folder.get_text(),
							prefix + self.entry_pattern.get_text())
		
		# Do clean-up
		self.hide()
		
		return result

#
# Strip download dialog
#

class DownloadStrips(gtk.Dialog):
	def __init__(self, parent=None):
		gtk.Dialog.__init__(self, 'Webcomic Downloader - Downloading strips', parent, gtk.DIALOG_MODAL|gtk.DIALOG_DESTROY_WITH_PARENT)
		self.connect('response', self.callback_response)
		
		# Create the Stop button
		self.button_stop = gtk.Button(stock=gtk.STOCK_STOP)
		self.button_stop.connect('clicked', self.callback_stop)
		self.get_action_area().pack_start(self.button_stop, True, False, 0)
		
		# Create the Close button
		self.button_close = gtk.Button(stock=gtk.STOCK_CLOSE)
		self.button_close.set_sensitive(False)
		self.button_close.connect('clicked', self.callback_close)
		self.get_action_area().pack_start(self.button_close, True, False, 0)
		
		# Create the TextView
		self.text_buffer = gtk.TextBuffer()
		self.text_view = gtk.TextView(self.text_buffer)
		self.text_view.set_editable(False)
		self.scroller = gtk.ScrolledWindow()
		self.scroller.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_ALWAYS)
		self.scroller.add(self.text_view)
		self.get_content_area().add(self.scroller)
		
		self.running = True
	
	def callback_response(self, widget, data=None):
		pass
	
	def callback_stop(self, widget, data=None):
		self.running = False
		pass
	
	def callback_close(self, widget, data=None):
		self.response(gtk.RESPONSE_REJECT)
	
	def callback_grab(self, widget, data=None):
		result = self.running
		try:
			info = self.generator.next()
			if info[0] == None:
				# This is the first time through, fill in some information in the buffer
				self.text_buffer.set_text('%s\'s last-downloaded file was %s.\n'%(self.webcomic_name, str(info[1])))
			elif info[0]:
				self.text_buffer.insert(self.text_buffer.get_end_iter(), 'Successfully downloaded strip %s.\n'%info[2])
			else:
				self.text_buffer.insert(self.text_buffer.get_end_iter(), 'Failed to download strip %s.\n'%info[2])
		except StopIteration:
			result = False
		except Exception as er:
			self.text_buffer.set_text('Unknown error: %s'%str(er))
			self.text_buffer.insert(self.text_buffer.get_end_iter(), '\n' + traceback.format_exc())
			print(er)
			print(traceback.format_exc())
			result = False
		
		if not result:
			self.button_close.set_sensitive(True)
			self.button_stop.set_sensitive(False)
		return result
	
	def run(self, name, folder, pattern, skipsafe):
		# Prep the dialog
		self.text_buffer.set_text('')
		self.webcomic_name = name
		self.webcomic_folder = folder
		self.webcomic_pattern = pattern
		self.webcomic_skipsafe = skipsafe
		
		# Check whether the strip uses only one image type or several
		self.webcomic_check_all = (pattern[1] == 'a')
		
		if self.webcomic_check_all:
			print('Checking all image formats.')
		else:
			print('Only one image format to download.')
		
		# Check whether the strip uses numeric or date-wise numbering
		if pattern[0] == 'n':
			self.generator = numeric_download(name, folder, pattern[3:], skipsafe, self.webcomic_check_all)
		else:
			print('Datewise webcomic downloading is not yet supported!')
			#self.generator = datewise_download(name, folder, pattern[3:], skipsafe, self.webcomic_check_all)
		
		running = True
		self.button_close.set_sensitive(False)
		self.button_stop.set_sensitive(True)
		
		# Start a timeout
		gobject.timeout_add(2000, self.callback_grab, 'grab')
		
		self.show_all()
		gtk.Dialog.run(self)
		
		# Shut-down the dialog
		self.hide()

#
# Main Window:
#
class MainWindow(gtk.Window):
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
		self.list_data = gtk.ListStore(gobject.TYPE_INT64,   # ID
										gobject.TYPE_STRING, # Name
										gobject.TYPE_STRING, # Folder
										gobject.TYPE_STRING, # Pattern
										gobject.TYPE_STRING, # Date added
										gobject.TYPE_INT64)  # Skipsafe

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
		self.list_data.clear()
		webcomics = db_list_webcomics()
		for comic in webcomics:
			self.list_data.append(comic)

	def callback_new(self, widget, data):
		# Show the Add a Webcomic dialog
		if a.run():
			# If the dialog returned True, reload the list
			self.reload_webcomic_list()

	def callback_open(self, widget, data):
		(model, pathlist) = self.list_view.get_selection().get_selected_rows()
		if 0 == len(pathlist):
			return
		else:
			tree_iter = model.get_iter(pathlist[0])
			ds.run(model.get_value(tree_iter, 1),
					model.get_value(tree_iter, 2),
					model.get_value(tree_iter, 3),
					model.get_value(tree_iter, 5))

	def callback_delete(self, widget, data):
		(model, pathlist) = self.list_view.get_selection().get_selected_rows()
		for path in pathlist:
			tree_iter = model.get_iter(path)
			print('Deleting webcomic with ID %d'%(model.get_value(tree_iter, 0)))
			#db_delete_webcomic(model.get_value(tree_iter, 0))
		self.reload_webcomic_list()

db_init()

mw = MainWindow()
mw.show_all()

a = AddWebcomic(mw)
ds = DownloadStrips(mw)

gtk.main()

