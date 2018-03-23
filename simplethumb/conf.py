import os
import tempfile

from appconf import AppConf
from django.conf import settings


class SimplethumbConf(AppConf):
    #: dictionary of preset names that have width and height values
    SIMPLETHUMB_PRESETS = {
        'thumbnail': '80x80,C',
        'medium': '320x240',
        'original': {},
    }

    SIMPLETHUMB_FORMAT_EXT_MAP = {
        'JPEG': 'jpg',
        'PNG': 'png',
    }

    SIMPLETHUMB_CACHE_ENABLED = True
    SIMPLETHUMB_CACHE_BACKEND_NAME = 'simplethumb'
    SIMPLETHUMB_CACHE_TTL = 3600 * 24 * 30  # 30 days
    SIMPLETHUMB_EXPIRE_HEADER = SIMPLETHUMB_CACHE_TTL

    settings.CACHES[SIMPLETHUMB_CACHE_BACKEND_NAME] = {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': os.path.join(tempfile.gettempdir(), 'django_simplethumb'),
        'TIMEOUT': SIMPLETHUMB_CACHE_TTL,
    }

    SIMPLETHUMB_DEFAULT_JPEG_QUALITY = 60

    SIMPLETHUMB_DEFAULT_OPTIMIZE_PNG = False

    SIMPLETHUMB_HMAC_KEY = settings.SECRET_KEY

    class Meta:
        prefix = 'simplethumb'
