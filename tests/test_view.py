from django.conf import settings
from django.test import TestCase
from django.utils.http import http_date

try:
    from unittest import mock
except ImportError:
    import mock

class TestView(TestCase):

    @mock.patch('simplethumb.models.os.stat')
    @mock.patch('time.time', mock.MagicMock(return_value=0))
    def get_image(self, url, mock_mtime):
        mock_mtime.return_value.st_mtime = settings.FAKE_TIME
        return self.client.get(url)

    def test_view_status_goodspec(self):
        resp = self.get_image('/cat.png.EcGFxfc.png')
        self.assertEqual(resp.status_code, 200)

    def test_view_last_modified(self):
        resp = self.get_image('/cat.png.EcGFxfc.png')
        self.assertEqual(resp['Last-Modified'], http_date(settings.FAKE_TIME))

    def test_view_expires(self):
        resp = self.get_image('/cat.png.EcGFxfc.png')
        self.assertEqual(resp['Expires'], http_date(settings.SIMPLETHUMB_EXPIRE_HEADER))

    def test_view_status_badspec(self):
        resp = self.get_image('/cat.png.xxxxxxx.png')
        self.assertEqual(resp.status_code, 404)
