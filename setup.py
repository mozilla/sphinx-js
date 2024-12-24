from io import open
from setuptools import setup


setup(
    name='sphinx-js',
    version='4.0.0',
    description='Support for using Sphinx on JSDoc-documented JS code',
    long_description=open('README.rst', 'r', encoding='utf8').read(),
    long_description_content_type="text/x-rst",
    license='MIT',
    packages=["sphinx_js"],
    url='https://github.com/mozilla/sphinx-js',
    include_package_data=True,
    install_requires=[
        'Jinja2>2.0',
        'parsimonious>=0.10.0,<0.11.0',
        'Sphinx>=5.0.0',
        'markupsafe',
    ],
    python_requires='>=3.9',
    classifiers=[
        'Framework :: Sphinx :: Extension',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Development Status :: 5 - Production/Stable',
        'License :: OSI Approved :: MIT License',
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        'Topic :: Documentation :: Sphinx',
        'Topic :: Software Development :: Documentation'
    ],
    keywords=['sphinx', 'documentation', 'docs', 'javascript', 'js', 'jsdoc', 'restructured', 'typescript', 'typedoc'],
)
