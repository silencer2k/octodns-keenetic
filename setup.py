#!/usr/bin/env python

from setuptools import find_packages, setup


def readme():
    with open("README.md") as fh:
        long_desc = fh.read()
        desc = long_desc.split("\n", 1)[0].lstrip("#").strip()
        return desc, long_desc


def version():
    with open("octodns_keenetic/__init__.py") as fh:
        for line in fh:
            if line.startswith("__version__"):
                return line.split('"')[1]
    return "unknown"


desc, long_desc = readme()

tests_require = ("pytest", "pytest-cov", "pytest-network", "requests_mock")

setup(
    author="Aleksandr Aleshin",
    author_email="silencer2k@gmail.com",
    description=desc,
    extras_require={
        "dev": tests_require
        + (
            # we need to manually/explicitely bump major versions as they're
            # likely to result in formatting changes that should happen in their
            # own PR. This will basically happen yearly
            # https://black.readthedocs.io/en/stable/the_black_code_style/index.html#stability-policy
            "black>=24.3.0,<25.0.0",
            "build>=0.7.0",
            "changelet",
            "isort>=5.11.5",
            "proviso",
            "pyflakes>=2.2.0",
            "readme_renderer[md]>=26.0",
            "twine>=3.4.2",
        ),
        "test": tests_require,
    },
    install_requires=(
        "octodns>=1.5.0",
        "requests>=2.27.0",
    ),
    license="MIT",
    long_description=long_desc,
    long_description_content_type="text/markdown",
    name="octodns-keenetic",
    packages=find_packages(),
    python_requires=">=3.9",
    tests_require=tests_require,
    url="https://github.com/silencer2k/octodns-keenetic",
    version=version(),
)
