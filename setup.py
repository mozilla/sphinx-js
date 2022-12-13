from io import open
from setuptools import setup, find_packages


setup(
    name='sphinx-js',
    version='3.2.0',
    description='Support for using Sphinx on JSDoc-documented JS code',
    long_description=open('README.rst', 'r', encoding='utf8').read(),
    long_description_content_type="text/x-rst",
    author='Erik Rose',
    author_email='erikrose@grinchcentral.com',
    license='MIT',
    packages=find_packages(exclude=['ez_setup']),
    url='https://github.com/mozilla/sphinx-js',
    include_package_data=True,
    install_requires=[
        'Jinja2>2.0',
        'parsimonious>=0.10.0,<0.11.0',
        'Sphinx>=4.1.0,<6.0.0',
        # Pin markupsafe because of
        # https://github.com/pallets/jinja/issues/1585
        'markupsafe==2.0.1',
    ],
    python_requires='>=3.7',
    classifiers=[
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Development Status :: 5 - Production/Stable',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Topic :: Documentation :: Sphinx',
        'Topic :: Software Development :: Documentation'
    ],
    keywords=['sphinx', 'documentation', 'docs', 'javascript', 'js', 'jsdoc', 'restructured', 'typescript', 'typedoc'],
)
