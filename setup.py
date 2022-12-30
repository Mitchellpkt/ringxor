#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import io
from glob import glob
from os.path import basename
from os.path import dirname
from os.path import join
from os.path import splitext
import re

from setuptools import find_packages
from setuptools import setup


def read(*names, **kwargs):
    with io.open(
        join(dirname(__file__), *names), encoding=kwargs.get("encoding", "utf8")
    ) as fh:
        return fh.read()


setup(
    name="ringxor",
    version="0.0.2.2",
    license="MIT",
    description="Tooling for passive deanonymization of Monero-style blockchains using differ-by-one ring comparisons",
    long_description=read("README.rst"),
    author="Isthmus (Mitchell P. Krawiec-Thayer)",
    author_email="ringxor@mitchellpkt.com",
    url="https://github.com/mitchellpkt/ringxor",
    packages=find_packages("src"),
    package_dir={"": "src"},
    py_modules=[splitext(basename(path))[0] for path in glob("src/*.py")],
    include_package_data=True,
    zip_safe=False,
    classifiers=[
        # complete classifier list: http://pypi.python.org/pypi?%3Aaction=list_classifiers
        "Intended Audience :: Developers",
        'License :: OSI Approved :: MIT License',
        "Operating System :: Unix",
        "Operating System :: POSIX",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: MacOS :: MacOS X",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: Implementation :: PyPy",
        "Topic :: Utilities",
    ],
    project_urls={
        "Changelog": "https://github.com/mitchellpkt/ringxor/blob/main/CHANGELOG.rst",
        "Issue Tracker": "https://github.com/mitchellpkt/ringxor/issues",
    },
    keywords=[
        "monero",
        "chainanalysis",
        "chainalysis",
        "blockchain",
        "deanonymization",
        "ringxor",
    ],
    python_requires=">=3.8",
    install_requires=[
        "numpy",
    ],
    extras_require={},
    # entry_points={
    #     "console_scripts": [
    #         "isthmuslib = isthmuslib.cli:main",
    #     ]
    # },
)
