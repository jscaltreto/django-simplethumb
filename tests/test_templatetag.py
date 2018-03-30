import os
from django.template import Template, Context
from django.test import TestCase

try:
    from unittest import mock
except ImportError:
    import mock


class TestTemplateTag(TestCase):
    TEMPLATE = Template('{% load simplethumb_tags %}{% simplethumb image spec %}')

    @mock.patch('simplethumb.models.os.stat')
    def test_template_tag(self, mock_mtime):
        mock_mtime.return_value.st_mtime = '1234567890'
        rendered = self.TEMPLATE.render(Context({'image': 'cat.png', 'spec': ''}))

        self.assertEqual(rendered, '/cat.png.EcGFxfc.png')
