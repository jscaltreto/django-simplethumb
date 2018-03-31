import mimetypes
import time

from django.http import HttpResponse, Http404, HttpResponseNotModified
from django.utils.http import http_date
from django.views.static import was_modified_since

from django.conf import settings
from simplethumb.models import Image
from simplethumb.spec import Spec, ChecksumException, decode_spec


# noinspection PyUnusedLocal
def serve_image(request, basename, encoded_spec, ext):
    try:
        image = Image(url=basename)
    except OSError:
        raise Http404()

    try:
        spec = Spec.from_spec(
            decode_spec(encoded_spec, image.basename, image.mtime, settings.SIMPLETHUMB_HMAC_KEY )
        )
    except ChecksumException:
        raise Http404()

    image.spec = spec

    mimetype = mimetypes.guess_type(request.path)[0]
    if not was_modified_since(request.META.get('HTTP_IF_MODIFIED_SINCE'),
                              image.mtime, image.stat.st_size):
        return HttpResponseNotModified(content_type=mimetype)

    expire_time = settings.SIMPLETHUMB_EXPIRE_HEADER

    resp = HttpResponse(
        image.render(),
        mimetype
    )
    resp['Expires'] = http_date(time.time() + expire_time)
    resp['Last-Modified'] = http_date(image.mtime)

    return resp
