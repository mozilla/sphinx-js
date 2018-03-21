from recommonmark.transform import AutoStructify
from recommonmark.parser import CommonMarkParser


extensions = [
    'sphinx.ext.mathjax',
    'sphinx_js'
]

source_suffix = ['.rst', '.md']
master_doc = 'index'
author = 'Jam Risser'
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']
source_parsers = {
    '.md': CommonMarkParser
}

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
