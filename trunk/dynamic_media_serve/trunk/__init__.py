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
import mimetypes, time, datetime
import os, zlib, md5, random
import rfc822
import stat
import urllib, urllib2

from django.utils.text import compress_string as django_compress_string
from django.views import static as django_static
from django.core.cache import cache
from django.conf import settings
from django.template import RequestContext

if hasattr(settings, "CACHE_MIDDLEWARE_SECONDS") :
	CACHE_MIDDLEWARE_SECONDS = settings.CACHE_MIDDLEWARE_SECONDS
else :
	CACHE_MIDDLEWARE_SECONDS = 10

if hasattr(settings, "DMS_TMP_DIR") :
	DMS_TMP_DIR = settings.DMS_TMP_DIR
else :
	DMS_TMP_DIR = "/tmp/dms/"
	if not os.path.exists(DMS_TMP_DIR) :
		os.makedirs(DMS_TMP_DIR)

if hasattr(settings, "HTTP_EXPIRE_INTERVAL") :
	HTTP_EXPIRE_INTERVAL = settings.HTTP_EXPIRE_INTERVAL
else :
	HTTP_EXPIRE_INTERVAL = 10 * 24 * 60 * 60 # 10 days

if hasattr(settings, "DEFAULT_IMAGE_RENDER_MODE") :
	DEFAULT_IMAGE_RENDER_MODE = settings.DEFAULT_IMAGE_RENDER_MODE
else :
	DEFAULT_IMAGE_RENDER_MODE = "ratio"

import image

def serve (request, path, document_root=None, show_indexes=False, force_mimetype=None) :
	__argument = request.GET.copy()
	document_root = os.path.abspath(document_root)

	if force_mimetype is None :
		force_mimetype = __argument.get("force_mimetype", "").strip()

	use_cache = not __argument.has_key("update")
	if __argument.get("compress", "").lower() not in ("gzip", "deflate", ) :
		compress = None
	else :
		if True not in [i == compress for i in request.META.get("HTTP_ACCEPT_ENCODING", "").split(",") if i.strip()] :
			compress = None

	# for multibyte url handling.
	path0 = list()
	for i in path.split("/") :
		path0.append(urllib.unquote(str(i)))

	path = "/".join(path0)
	if path.startswith("http%3A%2F%2F") or path.startswith("http://") :
		fullpath = path
		func_get_media = get_media_external
	else :
		fullpath = os.path.abspath(os.path.join(document_root, path))

		# prevent to follow up the prior directory.
		if not fullpath.startswith(document_root) :
			response = HttpResponse("", status=401)
			return response

		if not os.path.exists(fullpath) :
			raise Http404, "'%s' does not exist" % fullpath

		if os.path.isdir(fullpath) : # DMS does not support directory index page.
			raise Http404, "Directory indexes are not allowed here."

		func_get_media = get_media_internal

	# for IE series, check 'HTTP_IF_NONE_MATCH' first.
	if not use_cache and \
			request.META.get("HTTP_IF_NONE_MATCH", None) == get_etag(fullpath) :
		return HttpResponseNotModified()
	elif not use_cache and not was_modified_since(request, fullpath) :
		return HttpResponseNotModified()
	else :
		if use_cache :
			# We use cache. If you did not enable the caching,
			# nothing will be happended.
			response = cache.get(get_cache_name(request, path))
			if response :
				return response

	(contents, mimetype, status_code, last_modified, ) = func_get_media( \
		request,
		fullpath,
		use_cache=use_cache,
		force_mimetype=force_mimetype,
	)

	if status_code == 304 :
		return HttpResponseNotModified()

	response = HttpResponse(
		compress and compress_string(contents, compress) or contents,
		mimetype=force_mimetype and force_mimetype or mimetype
	)
	response["Last-Modified"] = last_modified
	response["Expires"] = rfc822.formatdate(time.mktime((datetime.datetime.now() + datetime.timedelta(seconds=HTTP_EXPIRE_INTERVAL)).timetuple()))
	response["ETag"] = get_etag(fullpath)

	if compress :
		response["Content-Encoding"] = compress

	cache.set(
		get_cache_name(request, fullpath),
		response, CACHE_MIDDLEWARE_SECONDS,
	)

	return response

def was_modified_since (request, path) :
	statobj = os.stat(path)
	return django_static.was_modified_since(
		request.META.get("HTTP_IF_MODIFIED_SINCE", None),
		statobj[stat.ST_MTIME],
		statobj[stat.ST_SIZE]
	)

def get_mime_handler (mimetype) :
	if mimetype is None :
		return func_default

	__media_type = "func_%s" % mimetype.replace("/", "_").replace("-", "__")
	if globals().has_key(__media_type) :
		fn = globals().get(__media_type)
	else :
		__media_type = mimetype.split("/")[0]
		fn = globals().get("func_%s" % __media_type, func_default)

	return fn

def get_cache_name (request, path) :
	return urllib.quote("%s?%s" % (path, request.GET.urlencode()), "")

def get_etag (path) :
	try :
		mtime = os.stat(path)[stat.ST_MTIME]
	except :
		mtime = time.time()

	return urllib.quote(path + str(mtime), "")

def compress_string (s, mode="gzip") :
	if mode == "gzip" :
		return django_compress_string(s)
	elif mode == "deflate" :
		return zlib.compress(s)
	else :
		return s
from django.template import Template
def get_rendered_to_string (request, content) :
	if not request.GET.has_key("use_template") :
		return content
	else :
		try :
			t = Template(content)
			return t.render(RequestContext(request))
		except Exception, e :
			if settings.DEBUG :
				print e

			return content

##################################################
# Mimetype handler
def func_image (request, fd, path=None) :
	if path is None :
		return fd.read()

	__argument = request.GET.copy()

	__mode = __argument.get("mode", DEFAULT_IMAGE_RENDER_MODE, )
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

	return fd.read()

def func_application_x__javascript (request, fd, path=None) :
	return get_rendered_to_string(request, fd.read())

def func_text_html (request, fd, path=None) :
	return get_rendered_to_string(request, fd.read())

def func_text_css (request, fd, path=None) :
	return get_rendered_to_string(request, fd.read())

def func_default (request, fd, path=None) :
	return fd.read()

def get_media_external (request, path, use_cache=True, force_mimetype=None) :
	req = urllib2.Request(path)
	if request.META.get("HTTP_REFERER", None) :
		req.add_header("Referer", request.META.get("HTTP_REFERER"))

	if request.META.get("HTTP_IF_MODIFIED_SINCE", None) :
		req.add_header(
			"If-Modified-Since",
			request.META.get("HTTP_IF_MODIFIED_SINCE")
		)

	if request.META.get("HTTP_IF_NONE_MATCH", None) :
		req.add_header(
			"If-None-Match",
			request.META.get("HTTP_IF_NONE_MATCH")
		)

	try :
		r = urllib2.urlopen(req)
	except urllib2.HTTPError, e :
		(contents, mimetype, status_code, last_modified, ) = (
			"", None, e.code, e.headers.getheader("last-modified"), )
	else :
		if force_mimetype :
			mimetype = force_mimetype
		else :
			mimetype = r.headers.getheader("content-type")

		# save in tmp
		try :
			path = "%s/%s%s" % (
				DMS_TMP_DIR,
				md5.new(str(random.random())).hexdigest(),
				mimetypes.guess_extension(mimetype),
			)
			tmp = file(path, "w")
			tmp.write(r.read())
			tmp.close()
		except :
			return (r.read(), mimetype, status_code, last_modified, )

		last_modified = r.headers.getheader("last-modified")
		status_code = 200

		contents = get_mime_handler(mimetype)(request, file(path, "rb"), path=path)
		os.remove(path)

	return (contents, mimetype, status_code, last_modified, )

def get_media_internal (request, path, use_cache=True, force_mimetype=None) :
	# get media type
	if force_mimetype :
		mimetype = force_mimetype
	else :
		mimetype = mimetypes.guess_type(path)[0]

	contents = get_mime_handler(mimetype)(request, file(path, "rb"), path=path)

	return (
		contents,
		mimetype,
		200,
		rfc822.formatdate(os.stat(path)[stat.ST_MTIME]),
	)


"""
Description
-----------


ChangeLog
---------


Usage
-----


"""

__author__ =  "Spike^ekipS <spikeekips@gmail.com>"

