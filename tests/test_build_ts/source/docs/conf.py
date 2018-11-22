# -*- coding: utf-8 -*-
extensions = [
    'sphinx_js'
]

# Minimal stuff needed for Sphinx to work:
source_suffix = '.rst'
master_doc = 'index'
author = u'Erik Rose'
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

jsdoc_config_path = '../tsconfig.json'
js_language = 'typescript'
