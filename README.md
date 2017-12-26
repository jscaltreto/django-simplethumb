# Django Simplethumb - Resize an image on the fly

[![Build Status](https://api.travis-ci.org/jscaltreto/django-simplethumb.png)](http://travis-ci.org/jscaltreto/django-simplethumb)

Originally forked from django-imagefit (https://github.com/vinyll/django-imagefit)

This is an almost complete reworking of django-imagefit and it is not cross-compatable.

This implements a new template tag, `simplethumb`, which accepts two parameters:

* Image file - a string representing a static file, or an ImageFieldFile instance (represeting
an ImageField object).
* Spec - the specification for what conversions to run on the image.

The tag returns the URL to the generated thumbnail.

Like imagefit, the modified image isn't generated until it is requested by the browser. This
is accomplished by encoding the spec into the generated file name. Once requested, the encoded
spec is read in,  then the original image is read off disk, processed, and the thumbnail
returned. The option (enabled by default) cache mechanism ensures that repeated requests
for the same image won't be reprocessed repeatedly.

Theoretically, a ne'er-do-well attacker could spam your server with requests for images of
varying sizes at significant CPU cost. To address this, some rudimentary security is included:
the spec includes a check-byte, and is obfuscated by XORing an HMAC of the original image file
name and its modification time (for cache busting). If the checksum fails, a 404 is returned.

Using the cache has the benefit that once a thumbnail becomes unreferenced
it will eventually expire.

I've only tested this in python 2.7, but I tried to make it python 3.x compatable
as much as possible, someone can report back and/or PR.


#### Benefits

* Base image remains untouched on the server, and no new files are generated (except
in the cache).
* For static images, it uses django's staticfiles finder to locate the image on disk.
* Define preset specs in your settings.py and reference them by name in your templates.
* No database requirements, new or modified models, etc.
* perfect match with mediaqueries to adapt on mobile, tablets and
multi-size screens.
* better quality than html/css resizing and no large file download, great for
lower bandwidth.



#### Quick tour

Example 1: render _/static/myimage.png_ image at a maximum size of 200 x 150 px:

```html
{% simplethumb "myimage.png" "200x150" %}
```

Example 2: render model's _news.image_ as a thumbnail (assuming _thumbnail_ is a defined preset):

```html
{% simplethumb "news.image" "thumbnail" %}
```

Example 3: render _/static/myimage.png_ image at a maximum cropped size of 150 x 150 px:

```html
{{ simplethumb "myimage.png" "150x150,C" }}
```

Example 3: render _/static/myimage.png_ with a maximum height of 150 px and convert to jpeg:

```html
{{ simplethumb "myimage.png" "x150 jpg" }}
```

#### What this is not

* For creating specific model fields that resize image when model saves, see
[django-imagekit](https://github.com/matthewwithanm/django-imagekit)
* If you wish to avoid very large image on the server, consider resizing your original image
before uploading it.


## Installation

#### Download

Via pip ![latest version](https://pypip.in/v/django-imagefit/badge.png)

```bash
pip install django-simplethumb
```

or the bleeding edge version

```
pip install -e git+https://github.com/jscaltreto/django-simplethumb.git#egg=django-simplethumb
```

#### update INSTALLED_APPS

In _settings.py_, add _simplethumb_ in your INSTALLED_APPS

```python
INSTALLED_APPS = (
	…,
	'simplethumb',
)
```

#### urls.py

Simplethumb is a resize service, therefore include its urls.

Prefix it with whatever you want (here "simplethumb" for example):

```python
urlpatterns = urlpatterns('',
    …
    url(r'^simplethumb/', include('simplethumb.urls')),
)
```

## Configuration

#### Presets

Presets are configuration names that hold width and height (and maybe more later on).
Simplethumb is already shipped with 3 presets : _thumbnail_ (80x80), _medium_ (320x240)
and _original_ (no resizing).

You may override them or create new ones through settings.py


Custom presets examples :

```python
SIMPLETHUMB_PRESETS = {
    'thumbnail': '64x64,C',
    'my_preset1': '300x200 jpeg',
    'my_preset2': '100x',
}
```


#### Cache

Because resizing an image on the fly is expensive, django cache is enabled
by default.

You can customize the default cache preferences by overriding default values
described below via settings.py :

```python
# enable/disable server cache
SIMPLETHUMB_CACHE_ENABLED = True
# set the cache name specific to simplethumb with the cache dict
SIMPLETHUMB_CACHE_BACKEND_NAME = 'simplethumb'
# set the cache TTL (default is 30 days)
SIMPLETHUMB_CACHE_TTL = 3600 * 24 * 30

CACHES = {
    'simplethumb': {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': os.path.join(tempfile.gettempdir(), 'django_simplethumb')
        }
    }
```

Note that `CACHES` default values will be merge with yours from _settings.py_

#### Expires Header

Simplethumb comes with Expires header to tell the browser whether it should request the
resource from the server or use the cached version.
This has two core benefits. The browser will be using the cached version of the resource
in the second load and page load will be much faster. Also, it will require fewer requests to the server.

As a page score parameter, static resources used in a web page should be containing
an Expires information for better performance.

The default value of the expires header is the same as the cache TTL (30 days).
You can override this value via settings.py as:

```python
SIMPLETHUMB_EXPIRE_HEADER = 3600  # for 1 hour
```

#### Other Configuration Options

* `SIMPLETHUMB_DEFAULT_JPEG_QUALITY` - Default image quality to use when saving JPEG (default is 60)
* `SIMPLETHUMB_DEFAULT_OPTIMIZE_PNG` - Whether to optimize PNG files (default False)
* `SIMPLETHUMB_HMAC_KEY` - Key to use when generating the HMAC for encoding the spec. (Default is settings.SECRET_KEY)

## Usage
The spec string used with the tag can contain the following tokens. While some tokens may be combined,
some will conflict and could produce unexpected results. Common sense is encouraged (i.e. don't try
to convert an image to both JPEG and PNG at the same time).

* Resize Image - 'WxH' - Proportionally scale an image to fit within a box _W_ wide and _H_ high. e.g. `300x400`
* Fit to Width - 'Wx' - Proportionally scale an image to have width _W_. e.g. `300x`
* Fit to Height - 'xH' - Proportionally scale an image to have height _H_. e.g. `x400`
* Scale Image - 'P%' - Proportionally scale an image by _P_ percent. e.g. `50%`
* Crop Image - 'WxH,C - Scale an image to *fill* a box _W_ wide and _H_ high, cropping off any excess. e.g. '100x100,C'
* Convert image to JPEG - 'jpeg' - Convert an image to JPEG (optionally include a 'quality' setting between 1 and 100). e.g. 'jpeg80'
* Convert image to PNG - 'png' - Convert an image to PNG (optionally include the letter _O_ to optimize). e.g. 'pngO'
* Crop Image to Ratio - 'C_X_:_Y_' - Crops an image to the specified aspect ratio. This is performed before resizing. e.g. 'C16:9'

If you don't specify a format to convert to, the original image format will be used. Though it will be rerendered
using the default quality or optimization setting defined.

With the exception of 'Scale Image', none of the resize commands will _increase_ the size of an image. So if the
image is smaller than the specified bounds, the image will not be scaled. Also note that all crops are "center cropped"

Because the spec will ultimately be encoded in a small binary format for inclusion in the image url, there
are some hard limits on the sizes which can be specified. Anything higher than these limits will be truncated:

* Width and Height attributes are limited to 13 bits, meaning the maximum image size is 8191x8191px (about 67MP, pretty big).
* The Percent scale attribute is limited to 10 bits, meaning an image can only be scaled up to 1023%.
* Crop ratio is stored as a custom 16-bit unsigned floating point (5 bit exponent, 11 bit mantissa), so there are limits related to precission. It should be good enough for image cropping.

## Troubleshooting


### "decoder jpeg not available" on Mac OSX


You may have installed PIL through pip or easy_install that
does not install libjpeg dependency.

If so :

1. Uninstall pil via pip
2. Install pip via homebrew: `brew install pil`
3. Reinstall pil via pip: `pip install pil`

