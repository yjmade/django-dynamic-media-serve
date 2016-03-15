You can install the `Django Dynamic Media Serve` easily.

# Requirements #
  * Django :)
  * PIL - Python Image Library
  * rsvg - (optional) python-gnome2-desktop, [ftp://ftp.gnome.org/pub/GNOME/sources/gnome-python-desktop/](ftp://ftp.gnome.org/pub/GNOME/sources/gnome-python-desktop/)
  * Pycairo - (optional) Python bindings for cairo, http://www.cairographics.org/pycairo
  * ~~~jsmin (optional) (`Django Dynamic Media Serve` alread include jsmin)~~~


# Download and Installation #
Check out the svn sources.
```
spike@spike:~/tmp$ svn checkout http://django-dynamic-media-serve.googlecode.com/svn/trunk/dynamic_media_serve/trunk dynamic_media_serve
A     ....
```

# Setup #
and then copy the `dynamic_media_serve` directory in you python path. To be easy work, just move it your django project directory.
```
spike@spike:~/django-runtime$ v
total 40
drwxr-xr-x 5 spike spike 4096 2008-01-18 00:58 .
drwxr-xr-x 5 spike spike  115 2008-01-18 00:53 ..
drwxr-xr-x 3 spike spike   65 2008-01-18 00:27 dynamic_media_serve
-rw-r--r-- 1 spike spike    0 2008-01-17 16:20 __init__.py
-rwxr-xr-x 1 spike spike  542 2008-01-17 16:20 manage.py
-rw-r--r-- 1 spike spike   30 2008-01-17 17:00 settings_local.py
-rw-r--r-- 1 spike spike 2852 2008-01-17 17:08 settings.py
-rw-r--r-- 1 spike spike  246 2008-01-18 00:26 urls.py
```

and edit the `urls.py`, this is my urls.py
```
from django.conf.urls.defaults import *

urlpatterns = patterns('',
	# Uncomment this for admin:
	#(r'^admin/', include('django.contrib.admin.urls')),
	(r"^__media__/(?P<path>.*)$", 
		"dynamic_media_serve.serve", {"document_root": "/home/spike/django-runtime/__media__"}
    ),
)
```

The first `__media__` is url prefix and the second is the absolute path of media repository.

After that, start your django.
```
spike@spike:~/django-runtime$ django-admin.py runserver
```

and then copy the image or any other files to `document_root` directory and check it in your web browser, http://<your IP>/media/<your file>

All is completed.

