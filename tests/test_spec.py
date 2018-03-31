import re

from django.conf import settings
from django.test import TestCase
from pprint import pprint

from simplethumb.spec import Spec, encode_spec, decode_spec


class TestFixtures(object):
    base_name = 'foo.jpg'
    mtime = settings.FAKE_TIME
    hmac_key = 'TESTKEY'
    known_specs = [
        ('451x154',
         'arRQwLc',
         {'height': True, 'width': True},
         {'height': 154, 'width': 451}),
        ('202x', 'iKcRyac', {'width': True}, {'width': 202}),
        ('x899', 'zKcSgL8', {'height': True}, {'height': 899}),
        ('C321:123', 'oKcbcy8', {'crop_ratio': True}, {'crop_ratio': 2672}),
        ('c123:321', 'DaeFQS8', {'crop_ratio': True}, {'crop_ratio': 37954}),
        ('999x888,C',
         'KcgS5LY',
         {'crop': True, 'height': True, 'width': True},
         {'height': 888, 'width': 999}),
        ('888x999,c',
         'q9vye7Y',
         {'crop': True, 'height': True, 'width': True},
         {'height': 999, 'width': 888}),
        ('200%', 'kKcRy60', {'scale': True}, {'scale': 200}),
        ('50%', 'bqcRMa0', {'scale': True}, {'scale': 50}),
        ('png', 'e6cRAo8', {'image_fmt': True}, {'image_fmt': 1}),
        ('jpg', 'eKcRAY8', {'image_fmt': True}, {'image_fmt': 2}),
    ]

    @classmethod
    def gen_test_data(cls):
        '''
        This method is useful for regenerating the known_specs. Add an element with
        just a spec string and run this method to output new content for the
        known_specs list. Only run this if you know the Spec code is working.
        Bit of a chicken and an egg here.
        '''
        output = []
        for known_spec in cls.known_specs:
            spec_string = known_spec[0]
            spec = Spec.from_string(spec_string)
            encoded_spec = encode_spec(spec.encode(), cls.base_name, cls.mtime, cls.hmac_key)
            output.append(
                (spec_string, encoded_spec, spec.flags, spec.attrs)
            )
        pprint(output)

    @classmethod
    def make_tests(cls, spec_string, encoded_spec, spec_flags, spec_attrs):
        def test_spec_from_string(self):
            spec = Spec.from_string(spec_string)
            self.assertEqual(
                spec.flags,
                spec_flags
            )
            self.assertEqual(
                spec.attrs,
                spec_attrs
            )

        def test_spec_encode(self):
            spec = Spec.from_string(spec_string)
            self.assertEqual(
                encode_spec(spec.encode(), cls.base_name, cls.mtime, cls.hmac_key),
                encoded_spec)

        def test_spec_decode(self):
            spec_raw = decode_spec(encoded_spec, cls.base_name, cls.mtime, cls.hmac_key)
            spec = Spec.from_spec(spec_raw)
            self.assertEqual(
                spec.flags,
                spec_flags
            )
            self.assertEqual(
                spec.attrs,
                spec_attrs
            )

        return [test_spec_from_string, test_spec_encode, test_spec_decode]

    @classmethod
    def test_factory(cls):
        for test_spec in cls.known_specs:
            for test_method in cls.make_tests(*test_spec):
                test_name = test_method.__name__
                test_method.__name__ = '{}_{}'.format(test_name, re.sub('[^0-9a-zA-Z_]', '_', test_spec[0]))
                setattr(TestSpec, test_method.__name__, test_method)

class TestSpec(TestCase):
    pass

TestFixtures.test_factory()
