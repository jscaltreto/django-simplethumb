# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(
    name='django-simplethumb',
    version='0.3.0',
    description='Django template tag to do some basic image processing, and cache the resulting image',
    long_description=open('README.md').read(),
    author='Jake Scaltreto',
    author_email='jscaltreto@gmail.com',
    url='http://github.com/jscaltreto/django-simplethumb',
    license='BSD',
    packages=find_packages(),
    zip_safe=False,
    install_requires=['django', 'six', 'django-appconf', 'Pillow', ],
    test_requires=['mock', ],
    include_package_data=True,
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Utilities',
        'Framework :: Django',
    ]
)
