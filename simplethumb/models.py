from __future__ import division

import mimetypes
from base64 import b64encode

from PIL import Image as PilImage
from django.contrib.staticfiles import finders
from django.core.cache import caches

from simplethumb.conf import settings
from simplethumb.spec import Spec, LittleFloat

try:
    import BytesIO
except ImportError:
    from io import BytesIO
import os

image_cache = caches[settings.SIMPLETHUMB_CACHE_BACKEND_NAME]


class Image(object):
    PROCESS_ORDER = [Spec.TOKEN_CROP_RATIO, Spec.TOKEN_CROP, Spec.TOKEN_SCALE, Spec.TOKEN_WIDTH, Spec.TOKEN_HEIGHT,
                     Spec.TOKEN_IMAGEFMT]

    def __init__(self, url='', spec=None):
        self.original_url = url
        self.path = None
        self.stat = None
        self._find_fs_image()

        self._spec = None
        if spec:
            self.spec = spec

        self.save_params = {}
        self.image_format = ''
        self.pil = None

        self.jpeg_quality = settings.SIMPLETHUMB_DEFAULT_JPEG_QUALITY
        self.optimize_png = settings.SIMPLETHUMB_DEFAULT_OPTIMIZE_PNG

    @property
    def cached(self):
        return image_cache.get(self.cache_key)

    @property
    def basename(self):
        return self.original_url.lstrip('/')

    @property
    def ext(self):
        try:
            return Spec.FORMAT_EXT_MAP[self.spec.image_fmt]
        except KeyError:
            return os.path.splitext(self.original_url)[1].lstrip('.')

    @property
    def cache_key(self):
        return '.'.join([self.basename, b64encode(self.spec.encoded)])

    @property
    def url(self):
        return '.'.join([self.cache_key, self.ext])

    @property
    def spec(self):
        return self._spec

    @spec.setter
    def spec(self, preset=None):
        if isinstance(preset, Spec):
            self._spec = preset
        else:
            preset_string = getattr(settings, 'SIMPLETHUMB_PRESETS', {}).get(preset, None) or preset
            self._spec = Spec.from_string(preset_string)

    @property
    def mimetype(self):
        return mimetypes.guess_type(self)

    def _find_fs_image(self):
        image_path = finders.find(os.path.normpath(self.basename).lstrip('/'))
        if not image_path:
            image_path = os.path.join(
                settings.MEDIA_ROOT,
                self.basename.lstrip(settings.MEDIA_URL)
            )

        self.stat = os.stat(image_path)
        self.path = image_path

    def _resize(self, width=None, height=None):
        orig_width, orig_height = self.pil.size
        self.pil.thumbnail(
            (int(width or orig_width), int(height or orig_height)),
            PilImage.ANTIALIAS)

    def _scale(self):
        percent = self.spec.scale
        orig_width, orig_height = self.pil.size
        new_width = int(max(orig_width * (float(percent) / 100), 1))
        new_height = int(max(orig_height * new_width / orig_width, 1))
        self.pil = self.pil.resize((new_width, new_height), PilImage.ANTIALIAS)

    def _width(self):
        width = self.spec.width
        self._resize(width=width)

    def _height(self):
        height = self.spec.height
        self._resize(height=height)

    def _crop_to(self, width, height):
        img_w, img_h = self.pil.size
        # don't crop an image than is smaller than requested size
        if img_w <= width and img_h <= height:
            return
        self.pil = self.pil.crop((
            (img_w - width) / 2,
            (img_h - height) / 2,
            (img_w + width) / 2,
            (img_h + height) / 2,
        ))

    def _crop(self):
        width = self.spec.width
        height = self.spec.height

        if height >= width:
            self._height()
        else:
            self._width()
        self._crop_to(width, height)

    def _crop_ratio(self):
        new_ratio = LittleFloat.unpack(self.spec.crop_ratio)

        img_w, img_h = self.pil.size
        current_ratio = float(img_w) / img_h

        if current_ratio >= new_ratio:
            new_w = round(img_h * new_ratio)
            new_h = img_h
        else:
            new_h = round(img_w * (1 / new_ratio))
            new_w = img_w

        self._crop_to(new_w, new_h)

    def _image_fmt(self):
        getattr(self, '_{}'.format(Spec.FORMAT_MAP[self.spec.image_fmt]))(self.spec.formatarg)

    def _format_jpeg(self, quality=None):
        if self.pil.mode == 'RGBA':
            self.pil = self.pil.convert('RGB')
        self.image_format = 'JPEG'
        if quality:
            self.jpeg_quality = int(quality)

    def _format_png(self, optimize=None):
        self.image_format = 'PNG'
        if optimize:
            self.optimize_png = True

    def process_image(self):
        self.pil = PilImage.open(self.path)

        # force RGB
        if self.pil.mode not in ('L', 'RGB', 'LA', 'RGBA'):
            self.pil = self.pil.convert('RGB')

        self.image_format = self.pil.format

        for image_filter in self.PROCESS_ORDER:
            if getattr(self.spec, image_filter):
                getattr(self, '_{}'.format(image_filter))()

        if self.image_format == 'JPEG':
            self.save_params['quality'] = self.jpeg_quality

        if self.image_format == 'PNG':
            self.save_params['optimize'] = self.optimize_png

    def render(self):
        """
        Save the image to the cache if not cached yet.
        """

        if settings.SIMPLETHUMB_CACHE_ENABLED:
            cached_image = self.cached
            if cached_image:
                return cached_image

        self.process_image()

        # Store the image data in cache
        image_str = BytesIO()
        self.pil.save(image_str, self.image_format, **self.save_params)
        image_data = image_str.getvalue()
        if settings.SIMPLETHUMB_CACHE_ENABLED:
            image_cache.set(self.cache_key, image_data)
        image_str.close()
        return image_data
