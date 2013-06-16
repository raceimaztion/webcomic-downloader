#
# This module manages how a strip's data is collected.
# Both in grabbing a page's HTML data, but also in downloading a page's strip images.
#

from bs4 import BeautifulSoup
import os
import re
import urllib2
import urlparse

TODO = """
Stuff to do:
	Turn the comic-download-controlling method into something more generic so it can be used to start at the comic's main page and go backwards to meet up with its previous results.
"""

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

def grab_page(url):
	result = urllib2.urlopen(url)
	if result.getcode() == 200:
		return BeautifulSoup(result.read())
	else:
		return result.getcode()

def get_filename(url):
	"""Return the name of a file given its URL."""
	return url[1 + url.rfind('/'):]

#
# Comic-page manipulating functions:
#

def get_next(html):
	"""Given the BeautifulSoup source of a page, return the URL for the next one, or None if it can't be determined."""
	# First, try asking for the <link rel="next"> tag
	result = html.findAll('link', rel='next')
	if len(result) > 0:
		return result[0].get('href')
	
	# Next, try looking for an array of <img> tags that use any of a number of ALT or TITLE attributes
	result = html.findAll(matches_next)
	if len(result) > 0:
		return result[0].get('href')
	
	return None

def get_previous(html):
	"""Given the BeautifulSoup source of a page, return the URL for the previous one, or None if it can't be determined."""
	# First, try asking for the <link rel="prev"> tag
	result = html.findAll('link', rel='prev')
	if len(result) > 0:
		return result[0].get('href')
	
	# Next, try looking for an array of <img> tags that use any of a number of ALT or TITLE attributes
	result = html.findAll(matches_previous)
	if len(result) > 0:
		return result[0].get('href')
	
	return None

def get_strip_images(html):
	"""Given the BeautifulSoup source of a page, return the URL(s) for the page's strip images."""
	result = html.findAll('div', class_=re.compile('strip|comic', re.IGNORECASE))
	results = []
	for tag in result:
		results.extend(tag.findAll('img'))
	return [tag.get('src') for tag in results]

def matches_next(tag):
	MATCHERS = [re.compile(a, re.IGNORECASE) for a in ['next', 'tomorrow']]
	# If it's an <A> tag with a string as its only child:
	if tag.name == 'a' and tag.string != None:
		for m in MATCHERS:
			if m.match(tag.string) != None:
				return tag.get('href')
	
	# Look for an <IMG> tag's TITLE attribute
	for m in MATCHERS:
		for t in tag.findAll('img', title=m):
			return tag.get('href')
		for t in tag.findAll('img', alt=m):
			return tag.get('href')
	
	return None

def matches_previous(tag):
	MATCHERS = [re.compile(a, re.IGNORECASE) for a in ['prev', 'yesterday', 'back']]
	# If it's an <A> tag with a string as its only child:
	if tag.name == 'a' and tag.string != None:
		for m in MATCHERS:
			if m.match(tag.string) != None:
				return tag.get('href')
	
	# Look for an <IMG> tag's TITLE attribute
	for m in MATCHERS:
		for t in tag.findAll('img', title=m):
			return tag.get('href')
		for t in tag.findAll('img', alt=m):
			return tag.get('href')
	
	return None

def absolute_url(page_url, relative_url):
	if page_url == None:
		return relative_url
	elif relative_url == None:
		return None
	elif type(relative_url) == list:
		return [absolute_url(page_url, url) for url in relative_url]
	else:
		return urlparse.urljoin(page_url, relative_url)

#
# Download-control function:
#

def strip_downloader(folder, first_page_url):
	next_page_url = first_page_url
	page_url = ''
	
	while next_page_url != None and next_page_url != page_url:
		page_url = next_page_url
		page_html = grab_page(page_url)
		if type(page_html) == int:
			print('Failed to download URL: %s\nError code was: %d'%(first_pag_url, page_html))
			yield (page_html, page_url, None)
			return
		page_images = absolute_url(page_url, get_strip_images(page_html))
		yield (200, page_url, page_images)
		# Download all the images
		for image in page_images:
			wget(image, folder)
		next_page_url = absolute_url(page_url, get_next(page_html))
	
	return
