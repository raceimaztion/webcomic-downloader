webcomic-downloader
===================

A simple downloader for the automated downloading of webcomic archives for Python and GTK.

Its end goal is to allow the user to list a bunch of webcomics and have the program download all the comic strip images with as little user direction as possible.

Note that this will require great intelligence on the part of the detection algorithm.

Notes, as of January 28, 2015:
------------------------------

I am in the process of rewriting the front-end code to use Python 3 and GTK 3. The goal is to make it extremely flexible and powerful, but still relatively easy to use.

A word of warning, however, apparently there are some websites that will prevent the current method of downloading comics by 403, Access Forbidden, error messages. Once I have the front-end rewritten sufficiently, I will also begin rewriting the downloader engine in an attempt to get around this issue.
