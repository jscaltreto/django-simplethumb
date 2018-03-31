import io

from PIL import Image as PILImage
from django.conf import settings
from django.core.cache import caches
from django.test import TestCase

from simplethumb.models import Image


class TestImageProcessing(TestCase):
    def setUp(self):
        caches[settings.SIMPLETHUMB_CACHE_BACKEND_NAME].clear()

    def render_image(self, spec, image_name='cat.png'):
        image = Image(url=image_name, spec=spec)
        image_data = image.render()
        return PILImage.open(io.BytesIO(image_data))

    def test_resize_width(self):
        image = self.render_image('100x')
        self.assertEqual(image.size[0], 100)

    def test_resize_height(self):
        image = self.render_image('x100')
        self.assertEqual(image.size[1], 100)

    def test_resize_width_height(self):
        image = self.render_image('100x100')
        self.assertEqual(image.size, (67,100))

    def test_square_crop(self):
        image = self.render_image('100x C1:1')
        self.assertEqual(image.size, (100,100))

    def test_crop(self):
        image = self.render_image('x100 C15:10')
        self.assertAlmostEqual(float(image.size[0]) / image.size[1], 1.5, delta=0.1)

    def test_image_format_jpeg(self):
        image = self.render_image('jpeg')
        self.assertEqual(image.format, 'JPEG')
        self.assertEqual(image.mode, 'RGB')

    def test_image_format_png(self):
        image = self.render_image('png', 'fruits.jpg')
        self.assertEqual(image.format, 'PNG')

    def test_image_scale(self):
        image = self.render_image('200%')
        self.assertEqual(image.size, (980, 1466))



