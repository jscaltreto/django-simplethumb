import binascii
import re


class ChecksumException(Exception):
    pass


class LittleFloat(object):
    """
    This is for converting aspect ratios (represented as a decimal)
    to a 16-bit binary representation and vice versa. The resulting
    format is a non-standard float.

    I'm not a computer scientist, but this seems to work.
    """
    BASE = 2
    MANT_BITS = 11
    EXP_BITS = 4
    SIZE = MANT_BITS + EXP_BITS + 1

    @classmethod
    def pack(cls, num):
        num = float(num)
        integral = int(num)
        dec = num - integral
        int_bin = '{0:b}'.format(integral) if integral > 0 else ''
        mantissa = int_bin
        for idx in range(cls.MANT_BITS - len(int_bin) + 1):
            if dec == 0:
                break
            next_val = float(dec * cls.BASE)
            next_bit = int(next_val)
            mantissa += str(next_bit)
            dec = next_val - next_bit

        if integral:
            exp = len(int_bin) - 1
            sign = '0'
        else:
            exp = mantissa.find('1') + 1
            sign = '1'
            if exp == -1:
                raise ValueError('Not enough precision {}'.format(num))
            mantissa = mantissa[exp - 1:]

        if exp >= (cls.BASE ** cls.EXP_BITS):
            raise ValueError('Not enough precision {}'.format(num))

        bin_str = sign + '{0:b}'.format(exp).zfill(cls.EXP_BITS)[:cls.EXP_BITS] \
            + mantissa[1:].ljust(cls.MANT_BITS, '0')[:cls.MANT_BITS]

        return int(bin_str, cls.BASE)

    @classmethod
    def unpack(cls, packed):
        bin_str = '{0:b}'.format(packed)[-cls.SIZE:].zfill(cls.SIZE)
        sign = int(bin_str[0])
        exp = int(bin_str[1:cls.EXP_BITS + 1], cls.BASE)
        if sign:
            exp *= -1
        mantissa = '1' + bin_str[1 + cls.EXP_BITS:]
        number = float()
        for idx in range(len(mantissa)):
            if mantissa[idx:idx + 1] == '1':
                number += cls.BASE ** (exp - idx)
        return number


class Spec(object):
    """
    Representation of an image format storage
    """

    TOKEN_FORMAT_JPEG = 'format_jpeg'
    TOKEN_FORMAT_PNG = 'format_png'
    TOKEN_CROP = 'crop'
    TOKEN_SCALE = 'scale'
    TOKEN_RESIZE = 'resize'
    TOKEN_WIDTH = 'width'
    TOKEN_HEIGHT = 'height'
    TOKEN_FORMATARG = 'formatarg'
    TOKEN_IMAGEFMT = 'image_fmt'
    TOKEN_CROP_RATIO = 'crop_ratio'
    TOKEN_CROP_RATIO_WIDTH = 'crop_ratio_width'
    TOKEN_CROP_RATIO_HEIGHT = 'crop_ratio_height'

    TOKEN_SPEC = [
        # token key, string match, kwarg match
        (TOKEN_FORMAT_JPEG, 'jpe?g(\d*)'),
        (TOKEN_FORMAT_PNG, 'png([Oo])?'),
        (TOKEN_CROP, '(\d+)x(\d+),[Cc]'),
        (TOKEN_SCALE, '(\d+(?:\.\d*)?)\%'),
        (TOKEN_RESIZE, '(\d+)x(\d+)'),
        (TOKEN_WIDTH, '(\d+)x'),
        (TOKEN_HEIGHT, 'x(\d+)'),
        (TOKEN_CROP_RATIO, '[Cc](\d+):(\d+)')
    ]

    FORMAT_UNDEF = 0
    FORMAT_PNG = 1
    FORMAT_JPEG = 2

    FORMAT_MAP = {
        FORMAT_PNG: TOKEN_FORMAT_PNG,
        FORMAT_JPEG: TOKEN_FORMAT_JPEG,
    }
    FORMAT_EXT_MAP = {
        FORMAT_JPEG: 'jpg',
        FORMAT_PNG: 'png',
    }

    HEADER_FMT = [
        (TOKEN_CROP, 1),
        (TOKEN_SCALE, 1),
        (TOKEN_RESIZE, 1),
        (TOKEN_WIDTH, 1),
        (TOKEN_HEIGHT, 1),
        (TOKEN_IMAGEFMT, 1),
        (TOKEN_FORMATARG, 1),
        (TOKEN_CROP_RATIO, 1),
    ]
    HEADER_LENGTH = sum([v for k, v in HEADER_FMT])
    VALID_HEADERS = [k for k, v in HEADER_FMT]

    # (spec attribute, size in bits)
    ATTR_FORMATS = {
        TOKEN_HEIGHT: 13,
        TOKEN_WIDTH: 13,
        TOKEN_SCALE: 10,
        TOKEN_IMAGEFMT: 3,
        TOKEN_FORMATARG: 7,
        TOKEN_CROP_RATIO: 16,
    }

    def __init__(self, flags, attrs):
        self.flags = flags
        self.attrs = attrs
        self.encoded = self.encode()

    def __getattribute__(self, item):
        try:
            attr = super(Spec, self).__getattribute__(item)
        except AttributeError as e:
            if item in self.VALID_HEADERS:
                try:
                    return self.attrs[item]
                except KeyError:
                    return self.flags.get(item, 0)
            else:
                raise e
        else:
            return attr

    @staticmethod
    def _check_val(value, size):
        if value > 2 ** size - 1:
            value = 2 ** size - 1
        return value

    @staticmethod
    def make_checksum(specbytes):
        return chr(sum(map(ord, specbytes)) % 255)

    def encode(self):
        packed_int = 0
        header_pos = 0
        body_pos = self.HEADER_LENGTH

        for attr, size in self.HEADER_FMT:
            value = self._check_val(int(self.flags.get(attr, 0)), size)
            packed_int += (value << header_pos)
            header_pos += size
            if value and attr in self.ATTR_FORMATS.keys():
                attr_val = int(self.attrs.get(attr, 0))
                attr_val_size = self.ATTR_FORMATS[attr]
                attr_val = self._check_val(attr_val, attr_val_size)
                packed_int += (attr_val << body_pos)
                body_pos += attr_val_size

        hex_str = format(packed_int, 'x').zfill(8)  # Pad to at least 4 bytes
        specbytes = binascii.unhexlify(('0' * (len(hex_str) % 2)) + hex_str)
        checksum = self.make_checksum(specbytes)
        return checksum + specbytes

    @classmethod
    def from_spec(cls, data):
        checkbyte, specbytes = data[:1], data[1:]
        checksum = cls.make_checksum(specbytes)
        if checksum != checkbyte:
            raise ChecksumException
        packed_int = int(binascii.hexlify(specbytes), 16)
        flags_dict = {}
        attrs_dict = {}
        header_pos = 0
        body_pos = cls.HEADER_LENGTH
        for attr, size in cls.HEADER_FMT:
            mask = (2 ** size - 1 << header_pos)
            value = (packed_int & mask) >> header_pos
            flags_dict[attr] = value
            header_pos += size
            if value and attr in cls.ATTR_FORMATS.keys():
                attr_val_size = cls.ATTR_FORMATS[attr]
                mask = (2 ** attr_val_size - 1 << body_pos)
                attrs_dict[attr] = (packed_int & mask) >> body_pos
                body_pos += attr_val_size
        return cls(flags_dict, attrs_dict)

    @classmethod
    def from_string(cls, filter_string):
        applied_filters = []
        tokens = filter_string.split()
        for preset_key, spec in cls.TOKEN_SPEC:
            r = re.compile("^{}$".format(spec))
            applied_filters += list(map(lambda t: (preset_key, r.match(t)), tokens))
        applied_filters = [(f[0], f[1].groups()) for f in applied_filters if f[1]]
        attrs_dict = {}
        flags_dict = {}
        for filterkey, args in applied_filters:
            if filterkey == cls.TOKEN_WIDTH:
                flags_dict[cls.TOKEN_WIDTH] = True
                attrs_dict[cls.TOKEN_WIDTH] = int(args[0])
            elif filterkey == cls.TOKEN_HEIGHT:
                flags_dict[cls.TOKEN_HEIGHT] = True
                attrs_dict[cls.TOKEN_HEIGHT] = int(args[0])
            elif filterkey == cls.TOKEN_RESIZE:
                flags_dict[cls.TOKEN_WIDTH] = True
                flags_dict[cls.TOKEN_HEIGHT] = True
                attrs_dict[cls.TOKEN_WIDTH] = int(args[0])
                attrs_dict[cls.TOKEN_HEIGHT] = int(args[1])
            elif filterkey == cls.TOKEN_CROP:
                flags_dict[cls.TOKEN_CROP] = True
                flags_dict[cls.TOKEN_WIDTH] = True
                flags_dict[cls.TOKEN_HEIGHT] = True
                attrs_dict[cls.TOKEN_WIDTH] = int(args[0])
                attrs_dict[cls.TOKEN_HEIGHT] = int(args[1])
            elif filterkey == cls.TOKEN_FORMAT_JPEG:
                flags_dict[cls.TOKEN_IMAGEFMT] = True
                attrs_dict[cls.TOKEN_IMAGEFMT] = cls.FORMAT_JPEG
                if args[0]:
                    flags_dict[cls.TOKEN_FORMATARG] = True
                    attrs_dict[cls.TOKEN_FORMATARG] = args[0]
            elif filterkey == cls.TOKEN_FORMAT_PNG:
                flags_dict[cls.TOKEN_IMAGEFMT] = True
                attrs_dict[cls.TOKEN_IMAGEFMT] = cls.FORMAT_PNG
                if args[0]:
                    flags_dict[cls.TOKEN_FORMATARG] = True
                    attrs_dict[cls.TOKEN_FORMATARG] = bool(args[0])
            elif filterkey == cls.TOKEN_SCALE:
                flags_dict[cls.TOKEN_SCALE] = True
                attrs_dict[cls.TOKEN_SCALE] = int(args[0])
            elif filterkey == cls.TOKEN_CROP_RATIO:
                flags_dict[cls.TOKEN_CROP_RATIO] = True
                ratio = float(args[0]) / int(args[1])
                attrs_dict[cls.TOKEN_CROP_RATIO] = LittleFloat.pack(ratio)
        return cls(flags_dict, attrs_dict)
