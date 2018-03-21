#!/usr/bin/env python3

from recommonmark.transform import AutoStructify
from recommonmark.parser import CommonMarkParser

author = 'Jam Risser'

copyright = '2018, Jam Risser'

exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

extensions = [
    'sphinx.ext.mathjax',
    'sphinx_js'
]

html_static_path = ['_static']

html_theme = 'sphinx_rtd_theme'

htmlhelp_basename = 'sphinx_hello_worlddoc'

language = None

master_doc = 'index'

needs_sphinx = '1.0'

#primary_domain = 'js'

project = 'sphinx-hello-world'

pygments_style = 'sphinx'

release = '0.0.1'

source_parsers = {
    '.md': CommonMarkParser
}

source_suffix = ['.rst', '.md']

templates_path = ['_templates']

todo_include_todos = False

version = '0.0.1'

def setup(app):
    app.add_config_value('recommonmark_config', {
        'auto_toc_tree_section': 'Content',
        'enable_auto_doc_ref': True,
        'enable_auto_toc_tree': True,
        'enable_eval_rst': True,
        'enable_inline_math': True,
        'enable_math': True
    }, True)
    app.add_transform(AutoStructify)
