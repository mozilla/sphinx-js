# Prevent spurious errors during `python setup.py test` in 2.6, a la
# http://www.eby-sarna.com/pipermail/peak/2010-May/003357.html:
try:
    import multiprocessing
except ImportError:
    pass

from io import open
from setuptools import setup, find_packages

long_description=open('README.rst', 'r', encoding='utf8').read()

setup(
    name='sphinx-js',
    version='1.4',
    description='Support for using Sphinx on JSDoc-documented JS code',
    long_description=long_description,
    author='Erik Rose',
    author_email='erikrose@grinchcentral.com',
    license='MIT',
    packages=find_packages(exclude=['ez_setup']),
    tests_require=['nose'],
    test_suite='nose.collector',
    url='https://github.com/erikrose/sphinx-js',
    include_package_data=True,
    install_requires=['docutils', 'Jinja2>2.0,<3.0', 'six<2.0', 'Sphinx<2.0'],
    classifiers=[
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3'
        ],
    keywords=['sphinx', 'documentation', 'docs', 'javascript', 'js', 'restructured'],
)
