After install the Django and `Django Dynamic Media Serve`, restart your web server.

# Post Installation #
## Locate Your Media ##
All the media files must be located in `document_root` directory of `urls.py`. This is my `urls.py` conf.
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
I set the `document_root` to `/home/spike/django-runtime/__media__` and I copy my media files to this directory.
```
spike@spike:~/django-runtime$ mkdir __media__
spike@spike:~/django-runtime$ cp /tmp/my_images/frontpage.png __media__
```

## Open up Your Browser and Check it ##
Open the location, `http://<domain>/__media__/frontpage.png`.
Do you see your image?

# Get Dynamically Resizing Or Cropping Image #
**Available Query String**
| **key** | **type** | **description** |
|:--------|:---------|:----------------|
| width   | integer  | thumbnail image width |
| height  | integer  | thumbnail image height |
| mode    | ''(default), 'flickr', 'sooa', 'topleft', 'topright', 'bottomleft', 'bottomright' | thumbnail style |
| update  |'1', '0'  | refresh         |
| compress|'1', '0'  | compress the output, gzip or deflate, which browser support |
| improve |'1', '0'  | when resizing 'gif' image, improve image quality using 'ALTIALIAS' filter. |
| force\_mimetype| 

&lt;mimetype&gt;

 | force to use this mimetype |

## Creating By Image Size Ratio ##
  * `http://<domain>/__media__/frontpage.png?width=<new width>&height=<new height>` : full query
  * `http://<domain>/__media__/frontpage.png?width=<new width>` : only width
  * `http://<domain>/__media__/frontpage.png?height=<new height>` : only height

## Creating Flicker Style Thumbnail ##
`http://<domain>/__media__/frontpage.png?width=<new width>&height=<new height>&mode=flickr`

## Cropping ##
  * `http://<domain>/__media__/frontpage.png?width=<new width>&height=<new height>&mode=topleft`
  * `http://<domain>/__media__/frontpage.png?width=<new width>&height=<new height>&mode=topright`
  * `http://<domain>/__media__/frontpage.png?width=<new width>&height=<new height>&mode=bottomleft`
  * `http://<domain>/__media__/frontpage.png?width=<new width>&height=<new height>&mode=bottomright`

## Convert SVG to PNG, JPEG, GIF ##
In the development version, we support 'svg' file converting to other image format, such as `PNG`, `JPEG`, `GIF` or other image format supported by `PIL`(`Python Image Library`).

To convert, add target format as `force_mimetype` in query string
  * `http://<domain>/__svg_to_png__/tiger.svg?force_mimetype=image/png`

You can also use other options, `width`, `height`, `mode` in there and external media
handling.
  * `http://<domain>/__svg_to_png__/tiger.svg?force_mimetype=image/png&width=100&height=200&mode=topleft`


  * SVG filter preserve the original transparent alpha channel.

# Get The Compressed Response For Performance #
**Available Query String**
| **key** | **type** | **description** |
|:--------|:---------|:----------------|
| compress | '1', '0' | set whether compress the script file or not |

# Access and Fetch the External Media #
It's so simple and support all feature of `Django Dynamic Media Serve`.
```
http://<domain>/__media__/<base64 encoded URL>?<available query string>
```

# Usages #
## Create your own media channel in urls.py ##
In the development version of `Django Dynamic Media Serve`, create your own channel,
which has default options.

I use `Django Dynamic Media Serve` to filter the svg to png with 100x100 size.

this is my urls.py.
```
urlpatterns = patterns("",
	....
	# fetch the image from flickr
	(
		r"^__flickr__/http://www.flickr.com/photos/smoothdude/(?P<path>.*)$",
		"dynamic_media_serve.serve",
		{
			"document_root": "/my_django_root/media/image/",
			"update": False,
			"compress": True,
			"width": 400,
			"height": 300,
		}
	),

	# convert svg to png with 100x100 size.
	(
		r"^__svg2png100x100__/(?P<path>.*)$",
		"dynamic_media_serve.serve",
		{
			"document_root": "/my_django_root/media/svg/",
			"update": False,
			"compress": True,
			"width": 100,
			"height": 100,
			"force_mimetype": "image/png",
		}
	),

	# css with i18n thru django template. It translate i18n message.
	(
		r"^__css_i18n__/(?P<path>.*)$",
		"dynamic_media_serve.serve",
		{
			"document_root": "/my_django_root/media/css/",
			"update": False,
			"compress": True,
			"use_template": True,
		}
	),
	....

```

## Cross-Domain Access ##
Most of the decent web browsers in these days can not allow to access the url over the domains like this. For examples, I run this script in <my domain>.com.
```
Ajax.Request(
 "http://<my domain>.com/get_my_profile/",
 {
  onComplete: function(request)
  {
    alert("success");
  }
);
```
it's ok, but this could not work,
```
Ajax.Request(
 "http://<my other managed domain>.com/get_my_profile/",
 {
  onFailure: function(request)
  {
    alert("failed to access");
  },
  onComplete: function(request)
  {
    alert("success");
  }
);
```

In this case, `Django Dynamic Media Serve` can give you the another way to access the other domains like this,
```
Ajax.Request(
 "http://<domain>/__media__/http%3A%2F%2F<my other managed domain>.com%2Fget_my_profile%2F",
 {
  onFailure: function(request)
  {
    alert("failed to access");
  },
  onComplete: function(request)
  {
    alert("success");
  }
);
```
The original url, `http://<my other managed domain>.com/get_my_profile/` was changed to `http%3A%2F%2F<my other managed domain>.com%2Fget_my_profile%2F`. To be clearly handle the URI, `Django Dynamic Media Serve` only get the `base64` encoded URI.
