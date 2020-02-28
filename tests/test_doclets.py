# -*- coding: utf-8 -*-
from os.path import abspath

try:
    from unittest.mock import Mock, patch
except ImportError:
    from mock import Mock, patch

import pytest
from sphinx.errors import SphinxError

from sphinx_js.doclets import doclet_full_path, root_or_fallback, gather_doclets, PathsTaken


def test_doclet_full_path():
    """Sanity-check doclet_full_path(), including throwing it a non-.js filename."""
    doclet = {
        'meta': {
            'filename': 'utils.jsm',
            'path': '/boogie/smoo/Checkouts/fathom',
        },
        'longname': 'best#thing~yeah'
    }
    assert doclet_full_path(doclet, '/boogie/smoo/Checkouts') == [
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
    assert root_or_fallback('smoo', ['a']) == abspath('smoo')


CONFLICTED_DOCLETS = [
    {
        'comment': True,
        'undocumented': False,
        'longname': 'best#thing~yeah',
        'meta': {
            'filename': 'utils.jsm',
            'path': '/boogie/smoo/Checkouts/fathom'
        }
    },
    {
        'comment': True,
        'undocumented': False,
        'longname': 'best#thing~yeah',
        'meta': {
            'filename': 'utils.jsm',
            'path': '/boogie/smoo/Checkouts/fathom'
        }
    },
    {
        'comment': True,
        'undocumented': False,
        'longname': 'best#thing~woot',
        'meta': {
            'filename': 'utils.jsm',
            'path': '/boogie/smoo/Checkouts/fathom'
        }
    },
    {
        'comment': True,
        'undocumented': False,
        'longname': 'best#thing~woot',
        'meta': {
            'filename': 'utils.jsm',
            'path': '/boogie/smoo/Checkouts/fathom'
        }
    }
]


def mock_analyze_jsdoc(doclets):
    def analyze(source_paths, app):
        return doclets
    return analyze


@patch(
    'sphinx_js.doclets.ANALYZERS', {
        'javascript': mock_analyze_jsdoc(CONFLICTED_DOCLETS)
    }
)
def test_gather_doclets_conflicted_lax():
    app = Mock()
    app.config.js_language = 'javascript'
    app.config.js_source_path = 'source-path'
    app.config.root_for_relative_js_paths = '/boogie/smoo/Checkouts/fathom'

    with patch('sphinx_js.doclets.logger', Mock()) as logger_mock:
        gather_doclets(app)

        message, = logger_mock.warning.call_args_list[0][0]
        assert './utils.best#thing~yeah' in message
        assert './utils.best#thing~woot' in message


@patch(
    'sphinx_js.doclets.ANALYZERS', {
        'javascript': mock_analyze_jsdoc(CONFLICTED_DOCLETS)
    }
)
def test_gather_doclets_conflicted():
    app = Mock()
    app.config.js_language = 'javascript'
    app.config.js_source_path = 'source-path'
    app.config.root_for_relative_js_paths = '/boogie/smoo/Checkouts/fathom'
    app.config.sphinx_js_lax = False

    with pytest.raises(PathsTaken) as e:
        gather_doclets(app)
    message = str(e.value)
    assert './utils.best#thing~yeah' in message
    assert './utils.best#thing~woot' in message


def test_gather_doclets_parse_error():
    app = Mock()
    app.config.js_language = 'javascript'
    app.config.js_source_path = 'source-path'
    app.config.root_for_relative_js_paths = '/boogie/smoo/Checkouts/fathom'
    app.config.sphinx_js_lax = True

    parse_error_doclet = {
        'comment': True,
        'undocumented': False,
        'longname': 'best#thing~yeah',
        'meta': {
            'filename': 'utils.jsm',
            'path': '../boogie/smoo/Checkouts/fathom'
        }
    }

    def patch_logger():
        return patch('sphinx_js.doclets.logger', Mock())

    def patch_analyze():
        return patch('sphinx_js.doclets.ANALYZERS', {
            'javascript': mock_analyze_jsdoc([parse_error_doclet])
        })

    with patch_logger() as logger_mock, patch_analyze():
        gather_doclets(app)

    message, = logger_mock.warning.call_args_list[0][0]
    assert 'Could not parse path correctly' in message
    assert 'boogie/smoo/Checkouts/fathom/utils.best#thing~yeah' in message
