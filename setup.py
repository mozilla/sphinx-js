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
    version='2.0',
    description='Support for using Sphinx on JSDoc-documented JS code',
    long_description=long_description,
    author='Erik Rose',
    author_email='erikrose@grinchcentral.com',
    license='MIT',
    packages=find_packages(exclude=['ez_setup']),
    tests_require=['nose',
                   # Sphinx's plain-text renderer changes behavior slightly
                   # with regard to how it emits class names in 1.6b1, which
                   # breaks our admittedly brittle tests. 1.6b2 has a bug that
                   # makes it crash on run, so we pin to 1.6b1.
                   'Sphinx==1.6b1'],
    test_suite='nose.collector',
    url='https://github.com/erikrose/sphinx-js',
    include_package_data=True,
    install_requires=['docutils', 'Jinja2>2.0,<3.0', 'parsimonious>=0.7.0,<0.8.0', 'six<2.0', 'Sphinx<2.0'],
    classifiers=[
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Development Status :: 5 - Production/Stable',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Topic :: Documentation :: Sphinx',
        'Topic :: Software Development :: Documentation'
        ],
    keywords=['sphinx', 'documentation', 'docs', 'javascript', 'js', 'jsdoc', 'restructured'],
)
