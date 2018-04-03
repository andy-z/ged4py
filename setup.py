#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

from setuptools import setup, find_packages

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = [
]

setup_requirements = [
]

test_requirements = [
]

setup(
    name='ged4py',
    version='0.1.6',
    description="GEDCOM tools for Python",
    long_description=readme + '\n\n' + history,

    author="Andy Salnikov",
    author_email='ged4py@py-dev.com',
    url='https://github.com/andy-z/ged4py',
    license="MIT License",

    packages=find_packages(include=['ged4py', 'ged4py.*']),
    entry_points={
        'console_scripts': [
        ]
    },
    include_package_data=False,

    install_requires=requirements,

    zip_safe=True,
    keywords='ged4py',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Sociology :: Genealogy',
    ],
    test_suite='tests',
    tests_require=test_requirements,
    setup_requires=setup_requirements,
)
