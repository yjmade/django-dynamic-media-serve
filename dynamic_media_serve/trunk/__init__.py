# -*- coding: utf-8 -*-
"""
 Copyright 2005 Spike^ekipS <spikeekips@gmail.com>

	This program is free software; you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation; either version 2 of the License, or
 (at your option) any later version.

 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with this program; if not, write to the Free Software
 Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
"""

from django.http import Http404, HttpResponse, HttpResponseNotModified
import mimetypes, time
import os, zlib, sha, random
import rfc822
import stat
import urllib, urllib2

from django.utils.text import compress_string as django_compress_string
from django.views import static as django_static
from django.core.cache import cache
from django.conf import settings

if hasattr(settings, "CACHE_MIDDLEWARE_SECONDS") :
	CACHE_MIDDLEWARE_SECONDS = settings.CACHE_MIDDLEWARE_SECONDS
else :
	CACHE_MIDDLEWARE_SECONDS = 10

if hasattr(settings, "DEFAULT_MODE") :
	DEFAULT_MODE = settings.DEFAULT_MODE
else :
	DEFAULT_MODE = "ratio"

try :
	from jsmin import jsmin
except :
	def jsmin (s) : return s

import image

def serve(request, path, document_root=None, show_indexes=False):
	__argument = request.GET.copy()
	__use_cache = not __argument.has_key("update")

	__compress = __argument.get("compress", "").lower()
	if __compress not in ("gzip", "deflate", ) :
		__compress = None
	else :
		if True not in [i == __compress for i in request.META.get("HTTP_ACCEPT_ENCODING", "").split(",")] :
			__compress = None

	if path.startswith("http%3A%2F%2F") :
		fullpath =  urllib.unquote(path)
		func_get_media = get_media_external
	else :
		fullpath = os.path.join(document_root, path)
		if os.path.isdir(fullpath):
			raise Http404, "Directory indexes are not allowed here."

		if not os.path.exists(fullpath):
			raise Http404, "'%s' does not exist" % fullpath

		func_get_media = get_media_internal

	(contents, mimetype, status_code, last_modified, response, ) = func_get_media(
		request, fullpath, use_cache=__use_cache)

	## Respect the If-Modified-Since header.
	if status_code == 304 :
		return HttpResponseNotModified()

	if not response :
		response = HttpResponse(
			__compress and compress_string(contents, __compress) or contents,
			mimetype=mimetype
		)
		response["Last-Modified"] = last_modified

		if __compress :
			response["Content-Encoding"] = __compress

		__path_cache = urllib.quote("%s?%s" % (fullpath, __argument.urlencode()), "")
		cache.set(__path_cache, response, CACHE_MIDDLEWARE_SECONDS)

	return response

def compress_string (s, mode="gzip") :
	if mode == "gzip" :
		return django_compress_string(s)
	elif mode == "deflate" :
		return zlib.compress(s)
	else :
		return s

def func_image (request, path) :
	__argument = request.GET.copy()

	__mode = __argument.get("mode", )
	__direction = __argument.get("direction", "center")
	__update = __argument.has_key("update")

	try :
		__width = int(__argument.get("width", None))
	except :
		__width = None
	else :
		__width = (__width > 0) and __width or None

	try :
		__height = int(__argument.get("height", None))
	except :
		__height = None
	else :
		__height = (__height > 0) and __height or None

	if __width or __height :
		try :
			return image.resize_image(
				path,
				(__width, __height, ),
				mode=__mode,
				direction=__direction
			)
		except Exception, e :
			print "[EE]" , e
			pass

	return open(path, "rb").read()

def func_application_x__javascript (request, path) :
	return jsmin(file(path).read())

def func_text_html (request, path) :
	return open(path, "rb").read()

def func_default (request, path) :
	return open(path, "rb").read()

def get_media_external (request, path, use_cache=True) :
	req = urllib2.Request(path)
	if request.META.get("HTTP_REFERER", None) :
		req.add_header("Referer", request.META.get("HTTP_REFERER"))

	if request.META.get("HTTP_IF_MODIFIED_SINCE", None) :
		req.add_header(
			"If-Modified-Since",
			request.META.get("HTTP_IF_MODIFIED_SINCE")
		)

	try :
		r = urllib2.urlopen(req)
	except urllib2.HTTPError, e :
		(contents, mimetype, status_code, last_modified, ) = (
			None, None, e.code, e.headers.getheader("last-modified"), )
	else :
		mimetype = r.headers.getheader("content-type")
		# save in tmp
		path = "/tmp/%s%s" % (
				sha.new(str(random.random())).hexdigest(),
				mimetypes.guess_extension(mimetype)
			)
		tmp = file(path, "w")
		tmp.write(r.read())
		tmp.close()

		last_modified = r.headers.getheader("last-modified")
		status_code = 200

		__media_type = "func_%s" % mimetype.replace("/", "_").replace("-", "__")
		if globals().has_key(__media_type) :
			fn = globals().get(__media_type)
		else :
			__media_type = mimetype.split("/")[0]
			fn = globals().get("func_%s" % __media_type, func_default)

		contents = fn(request, path)
		os.remove(path)

	return (contents, mimetype, status_code, last_modified, None, )

def get_media_internal (request, path, use_cache=True) :
	statobj = os.stat(path)
	(st_mtime, st_size, ) = (statobj[stat.ST_MTIME], statobj[stat.ST_SIZE], )

	if not django_static.was_modified_since(
			request.META.get("HTTP_IF_MODIFIED_SINCE", None), st_mtime, st_size) :
		status_code = 304
		mimetype = None
		contents = None
	else :
		status_code = 200

		if use_cache :
			__argument = request.GET.copy()

			# We use cache. If you did not enable the caching, nothing will be happended.
			__path_cache = urllib.quote("%s?%s" % (path, __argument.urlencode()), "")
			__response = cache.get(__path_cache)
			if __response :
				return (None, None, status_code, None, __response, )

		# get media type
		mimetype = mimetypes.guess_type(path)[0]

		__media_type = "func_%s" % mimetype.replace("/", "_").replace("-", "__")
		if globals().has_key(__media_type) :
			fn = globals().get(__media_type)
		else :
			__media_type = mimetype.split("/")[0]
			fn = globals().get("func_%s" % __media_type, func_default)

		contents = fn(request, path)

	return (contents, mimetype, status_code, rfc822.formatdate(st_mtime), None, )


"""
Description
-----------


ChangeLog
---------


Usage
-----


"""

__author__ =  "Spike^ekipS <spikeekips@gmail.com>"

