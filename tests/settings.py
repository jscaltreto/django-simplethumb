import os

SECRET_KEY = 'dummy'

INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.staticfiles',
    'simplethumb',
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}


ROOT_URLCONF = 'simplethumb.urls'

DEBUG = True

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'debug': True,
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

SECRET_KEY = 'DEFAULT_KEY'

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MEDIA_ROOT = os.path.join(BASE_DIR, 'tests', 'media')
MEDIA_PATH = '/media/'

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'tests', 'media'),
]
STATIC_URL = "/static/"

SIMPLETHUMB_CACHE_TTL = 60
SIMPLETHUMB_CACHE_ENABLED = True

FAKE_TIME = 1234567890
