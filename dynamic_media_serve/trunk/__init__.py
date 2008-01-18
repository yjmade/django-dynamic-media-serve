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
import mimetypes
import os, zlib
import rfc822
import stat
import urllib

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

	__compress = __argument.get("compress", "").lower()
	if __compress not in ("gzip", "deflate", ) :
		__compress = None
	else :
		if True not in [i == __compress for i in request.META.get("HTTP_ACCEPT_ENCODING", "").split(",")] :
			__compress = None

	fullpath = os.path.join(document_root, path)
	if os.path.isdir(fullpath):
		raise Http404, "Directory indexes are not allowed here."

	if not os.path.exists(fullpath):
		raise Http404, "'%s' does not exist" % fullpath

	## Respect the If-Modified-Since header.
	statobj = os.stat(fullpath)
	if not django_static.was_modified_since(
			request.META.get("HTTP_IF_MODIFIED_SINCE"),
			statobj[stat.ST_MTIME], statobj[stat.ST_SIZE]) :
		return HttpResponseNotModified()

    # We use cache. If you did not enable the caching, nothing will be happended.
	__path_cache = urllib.quote("%s?%s" % (path, __argument.urlencode()), "")
	__response = cache.get(__path_cache)
	if __response :
		return __response

	mimetype = mimetypes.guess_type(fullpath)[0]

	contents = get_media(request, fullpath, mimetype)
	response = HttpResponse(
		__compress and compress_string(contents, __compress) or contents,
		mimetype=mimetype
	)
	response["Last-Modified"] = rfc822.formatdate(statobj[stat.ST_MTIME])

	if __compress :
		response["Content-Encoding"] = __compress

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
			return image.resize_image(path,
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

def get_media (request, path, mimetype="text/plain") :
	# get media type
	__media_type = "func_%s" % mimetype.replace("/", "_").replace("-", "__")
	if globals().has_key(__media_type) :
		fn = globals().get(__media_type)
	else :
		__media_type = mimetype.split("/")[0]
		fn = globals().get("func_%s" % __media_type, func_default)

	return fn(request, path)


"""
Description
-----------


ChangeLog
---------


Usage
-----


"""

__author__ =  "Spike^ekipS <spikeekips@gmail.com>"
__version__=  "0.1"
__nonsense__ = ""

__file__ = "__init__.py"


