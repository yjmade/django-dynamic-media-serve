# Django Dynamic Media Serve #

`Django Dynamic Media Serve` is the good alternative of the default `django.views.static.serve` for serving the media files in Django. You can simply set just one line in `urls.py`.

At first, `Django Dynamic Media Serve` was developed for web album application, which handles enoumous image thumbnails and huge javascript files and each time when new files is added, creating thumbnail and compressing javascript files is so painful, so we wrote this `Django Dynamic Media Serve` to dynamically handle various media files in runtime without using any already-created file, especially image files.


# Feature #

## Various Media Serve thru Django ##
  * SVG
  * images(png, gif, jpeg, etc which can be supported by PIL).
  * javascript
  * any other files.

## External Media ##
If you need to fetch the media from outside of your media repository, `Django Dynamic Media Serve` support the ourside media. It can be useful for `Cross-Domain` access in `Ajax` script.

## Image Resizing and Croping ##
Using `PIL`(Imaging Python module), `Django Dynamic Media Serve` can create normal image thumbnail by image size ratio and can create the flicker style thumbnail.

## ~~~Javascript Compression~~~ ##
~~~`Django Dynamic Media Serve` can compress the javascript file using [jsmin](http://javascript.crockford.com/jsmin.html),.~~~
Django Media Server no longer does support javascript compression using jsmin because of the confirmed comment, '/**,**/' related problems.

## Support `If-Modified-Since`, `If-None-Match` ##
To respect the `If-Modified-Since` and `Etag`, `Django Dynamic Media Serve` can handle properly the `If-Modified-Since` and `If-None-Match` header variables.

## Caching ##
Support the native [Django caching system](http://www.djangoproject.com/documentation/cache/)