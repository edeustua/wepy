#!/usr/bin/env python
# -*- encoding: utf-8 -*-

from __future__ import absolute_import
from __future__ import print_function

from setuptools import setup, find_packages

import itertools as it

# setuptools only specifies abstract requirements. For the concrete
# requirements i.e. index or repo URL see requirements.txt
abstract_requirements = [
    'numpy',
    'h5py',
    'networkx>=2',
    'pandas',
    'dill',
    'click',
    'scipy',
    'geomm',
    'matplotlib',
    'tabulate',
    'jinja2',
    'pint',
    'multiprocessing_logging',
]

# extras requirements list
mdtraj_requirements = ['mdtraj']

#
examples_reqs = ['openmmtools']

# combination of all the extras requirements
all_requirements = it.chain.from_iterable([mdtraj_requirements, ])

setup(
    name='wepy',
    version='1.0.0-rc',
    author="Samuel D. Lotz",
    author_email="samuel.lotz@salotz.info",
    description="Weighted Ensemble Framework",
    #long_description=open('README.org').read(),
    license="MIT",
    url="https://github.com/ADicksonLab/wepy",
    classifiers=[
        "Topic :: Utilities",
        "License :: OSI Approved :: MIT License",
        'Programming Language :: Python :: 3'
    ],
    # building/dev
    setup_requires=['pytest-runner'],
    tests_require=['pytest', 'tox'],

    # package
    packages=find_packages(where='src'),

    package_dir={'' : 'src'},

    # if this is true then the package_data won't be included in the
    # dist. Use MANIFEST.in for this
    include_package_data=True,

    # pymodules is for single file standalone modules not part of the
    # package
    # py_modules=[],

    entry_points={
        'console_scripts' : ['wepy=wepy.cli:cli']
    },

    install_requires=abstract_requirements,

    extras_require={
        'mdtraj' : mdtraj_requirements,
        'all' : all_requirements,
    }
)
