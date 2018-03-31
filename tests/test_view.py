from django.conf import settings
from django.core.cache import caches
from django.test import TestCase
from django.utils.http import http_date

try:
    from unittest import mock
except ImportError:
    import mock

class TestView(TestCase):

    @mock.patch('simplethumb.models.Image.mtime', mock.PropertyMock(return_value=settings.FAKE_TIME))
    @mock.patch('time.time', mock.MagicMock(return_value=0))
    def get_image(self, url, kwargs={}):
        return self.client.get(url, **kwargs)

    def setUp(self):
        caches[settings.SIMPLETHUMB_CACHE_BACKEND_NAME].clear()

    def test_view_status_goodspec(self):
        resp = self.get_image('/cat.png.EcGFxfc.png')
        self.assertEqual(resp.status_code, 200)

    def test_view_last_modified(self):
        resp = self.get_image('/cat.png.EcGFxfc.png')
        self.assertEqual(resp['Last-Modified'], http_date(settings.FAKE_TIME))

    def test_view_expires(self):
        resp = self.get_image('/cat.png.EcGFxfc.png')
        self.assertEqual(resp['Expires'], http_date(settings.SIMPLETHUMB_EXPIRE_HEADER))

    def test_view_was_modified(self):
        resp = self.get_image(
            '/cat.png.EcGFxfc.png',
            {'HTTP_IF_MODIFIED_SINCE': http_date(settings.FAKE_TIME)}
        )
        self.assertEqual(resp.status_code, 304)

    def test_view_status_badspec(self):
        resp = self.get_image('/cat.png.xxxxxxx.png')
        self.assertEqual(resp.status_code, 404)

    def test_view_status_badimage(self):
        resp = self.get_image('/dog.png.xxxxxxx.png')
        self.assertEqual(resp.status_code, 404)
