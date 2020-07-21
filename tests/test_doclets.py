# -*- coding: utf-8 -*-
import pytest
from sphinx.errors import SphinxError

from sphinx_js.doclets import root_or_fallback
from sphinx_js.jsdoc import full_path_segments


def test_doclet_full_path():
    """Sanity-check full_path_segments(), including throwing it a non-.js filename."""
    doclet = {
        'meta': {
            'filename': 'utils.jsm',
            'path': '/boogie/smoo/Checkouts/fathom',
        },
        'longname': 'best#thing~yeah'
    }
    assert full_path_segments(doclet, '/boogie/smoo/Checkouts') == [
        './',
        'fathom/',
        'utils.',
        'best#',
        'thing~',
        'yeah',
    ]


def test_relative_path_root():
    """Make sure the computation of the root path for relative JS entity
    pathnames is right."""
    # Fall back to the only source path if not specified.
    assert root_or_fallback(None, ['a']) == 'a'
    with pytest.raises(SphinxError):
        root_or_fallback(None, ['a', 'b'])
    assert root_or_fallback('smoo', ['a']) == 'smoo'
