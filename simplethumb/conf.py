import base64
import hmac
import os
import tempfile
from itertools import izip, cycle

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


def calc_hmac(data):
    mac = hmac.new(str(settings.SIMPLETHUMB_HMAC_KEY))
    mac.update(data)
    return mac.digest()


def decode_spec(data, basename, mtime):
    padding_needed = len(data) % 4
    if padding_needed != 0:
        data += b'=' * (4 - padding_needed)
    decoded = base64.urlsafe_b64decode(str(data))
    sig = calc_hmac(basename + str(mtime))
    spec = xor_crypt_string(decoded, sig)
    return spec


def encode_spec(data, basename, mtime):
    sig = calc_hmac(basename + str(mtime))
    spec = xor_crypt_string(data, sig)
    encoded_spec = base64.urlsafe_b64encode(spec).rstrip('=')
    return encoded_spec


def xor_crypt_string(data, key):
    # Borrowed from https://stackoverflow.com/questions/11132714/python-two-way-alphanumeric-encryption
    return ''.join(chr(ord(x) ^ ord(y)) for (x, y) in izip(data, cycle(key)))
