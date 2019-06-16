"""Setup module for classify_bills

(derived from https://github.com/pypa/sampleproject)
"""

# Always prefer setuptools over distutils
from setuptools import setup, find_packages
import glob
import os
from os import path
# io.open is needed for projects that support Python 2.7
# It ensures open() defaults to text mode with universal newlines,
# and accepts an argument to specify the text encoding
# Python 3 only projects can skip this import
from io import open

here = path.abspath(path.dirname(__file__))


# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

# Arguments marked as "Required" below must be included for upload to PyPI.
# Fields marked as "Optional" may be commented out.

setup(
    name='classify_bills',
    version='1.0.0',
    description='Automatically sort and archive PDF bills and statements',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/abelikoff/classify_bills',
    author='Alexander L. Belikoff',
    author_email='abelikoff@gmail.com',

    # Classifiers help users find your project by categorizing it.
    #
    # For a list of valid classifiers, see https://pypi.org/classifiers/
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Intended Audience :: End Users/Desktop",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Operating System :: OS Independent",
        "Topic :: Utilities",
    ],
    keywords='bills management organize documents',
    # py_modules=["classify_bills"],
    packages=find_packages(exclude=['contrib', 'docs', 'tests']),
    # Specify which Python versions you support. In contrast to the
    # 'Programming Language' classifiers above, 'pip install' will check this
    # and refuse to install the project if the version does not match. If you
    # do not support Python 2, you can simplify this to '>=3.5' or similar, see
    # https://packaging.python.org/guides/distributing-packages-using-setuptools/#python-requires
    python_requires='>=3.5',

    # This field lists other packages that your project depends on to run.
    # Any package you put here will be installed by pip when your project is
    # installed, so they must be valid existing projects.
    #
    # For an analysis of "install_requires" vs pip's requirements files see:
    # https://packaging.python.org/en/latest/requirements.html
    # install_requires=['peppercorn'],  # Optional

    # List additional groups of dependencies here (e.g. development
    # dependencies). Users will be able to install these using the "extras"
    # syntax, for example:
    #
    #   $ pip install classify_bills[dev]
    #
    # Similar to `install_requires` above, these must be valid existing
    # projects.
    extras_require={  # Optional
        'dev': ['check-manifest'],
        'test': ['coverage'],
    },

    # data files to include
    data_files = [("classify_bills.config.examples",
                   sorted(glob.glob(path.join("config.examples", "*.xml"))))],

    # executable script
    entry_points={
        'console_scripts': [
            'classify_bills=classify_bills:main',
        ],
    },

    project_urls={  # Optional
        'Bug Reports': 'https://github.com/abelikoff/classify_bills/issues',
        'Source': 'https://github.com/abelikoff/classify_bills/',
    },
)
