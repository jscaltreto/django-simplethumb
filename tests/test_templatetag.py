import os

from django.conf import settings
from django.db.models.fields.files import ImageFieldFile, FileField
from django.template import Template, Context
from django.test import TestCase

try:
    from unittest import mock
except ImportError:
    import mock

THIS_DIR = os.path.dirname(os.path.abspath(__file__))


class TestTemplateTag(TestCase):
    TEMPLATE = Template('{% load simplethumb_tags %}{% simplethumb image spec %}')

    @mock.patch('simplethumb.models.Image.mtime', mock.PropertyMock(return_value=settings.FAKE_TIME))
    def test_template_tag_static(self):
        rendered = self.TEMPLATE.render(Context({'image': 'cat.png', 'spec': ''}))

        self.assertEqual(rendered, '/cat.png.EcGFxfc.png')

    @mock.patch('simplethumb.models.Image.mtime', mock.PropertyMock(return_value=settings.FAKE_TIME))
    def test_template_tag_imagefield(self):
        image = ImageFieldFile(instance=None, field=FileField(), name='cat.png')
        rendered = self.TEMPLATE.render(Context({'image': image, 'spec': ''}))

        self.assertEqual(rendered, '/cat.png.EcGFxfc.png')
