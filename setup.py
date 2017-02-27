# Copyright (C) 2017 Łukasz Langa

import ast
import os
import re
from setuptools import setup
import sys


assert sys.version_info >= (3, 5, 0), "flake8-mypy requires Python 3.5+"


current_dir = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(current_dir, 'README.md'), encoding='utf8') as ld_file:
    long_description = ld_file.read()


_version_re = re.compile(r'__version__\s+=\s+(?P<version>.*)')


with open(os.path.join(current_dir, 'flake8_mypy.py'), 'r') as f:
    version = _version_re.search(f.read()).group('version')
    version = str(ast.literal_eval(version))


setup(
    name='flake8-mypy',
    version=version,
    description="A plugin for flake8 integrating mypy.",
    long_description=long_description,
    keywords='flake8 mypy bugs linter qa typing',
    author='Łukasz Langa',
    author_email='lukasz@langa.pl',
    url='https://github.com/ambv/flake8-mypy',
    license='MIT',
    py_modules=['flake8_mypy'],
    zip_safe=False,
    install_requires=['flake8 >= 3.0.0', 'attrs', 'mypy'],
    test_suite='tests.test_mypy',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Framework :: Flake8',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Software Development :: Quality Assurance',
    ],
    entry_points={
        'flake8.extension': [
            'T4 = flake8_mypy:MypyChecker',
        ],
    },
)
