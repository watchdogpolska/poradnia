#!/usr/bin/env python


try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

import poradnia

version = poradnia.__version__

setup(
    name='poradnia',
    version=version,
    author='',
    author_email='naczelnik@jawnosc.tk',
    packages=[
        'poradnia',
    ],
    include_package_data=True,
    install_requires=[
        'Django>=1.7.10',
    ],
    zip_safe=False,
    scripts=['poradnia/manage.py'],
)
