from os.path import abspath

from nose.tools import assert_raises, eq_
from sphinx.errors import SphinxError

from sphinx_js.doclets import doclet_full_path, root_or_fallback


def test_doclet_full_path():
    """Sanity-check doclet_full_path(), including throwing it a non-.js filename."""
    doclet = {
        'meta': {
            'filename': 'utils.jsm',
            'path': '/boogie/smoo/Checkouts/fathom',
        },
        'longname': 'best#thing~yeah'
    }
    eq_(doclet_full_path(doclet, '/boogie/smoo/Checkouts'),
        ['./', 'fathom/', 'utils.', 'best#', 'thing~', 'yeah'])


def test_relative_path_root():
    """Make sure the computation of the root path for relative JS entity
    pathnames is right."""
    # Fall back to the only source path if not specified.
    eq_(root_or_fallback(None, ['a']), 'a')
    assert_raises(SphinxError, root_or_fallback, None, ['a', 'b'])
    eq_(root_or_fallback('smoo', ['a']), abspath('smoo'))
