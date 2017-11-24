import six
from django.core.urlresolvers import reverse
from django.db.models.fields.files import ImageFieldFile
from django.template import Library

from simplethumb.conf import encode_spec
from ..models import Image

register = Library()


@register.simple_tag
def simplethumb(value, spec=''):
    """
    Generates the url for the resized image prefixing with prefix_path
    return string url
    """

    if isinstance(value, ImageFieldFile):
        url = value.url
    elif isinstance(value, six.string_types):
        # A string is assumed to be a static file using django's staticfiles app
        url = value
    else:
        raise AttributeError("value is not a valid static image or ImageField")

    image = Image(url=url, spec=spec)
    encoded_spec = encode_spec(image.spec.encoded, image.basename, image.stat.st_mtime)

    return reverse('simplethumb', kwargs={
        'basename': image.basename,
        'encoded_spec': encoded_spec,
        'ext': image.ext,
    })
