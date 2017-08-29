from nose.tools import eq_

from sphinx_js.jsdoc import doclet_full_path


def test_doclet_full_path():
    """Sanity-check doclet_full_path(), including throwing it a non-.js filename."""
    doclet = {
        "meta": {
            "filename": "utils.jsm",
            "path": "/boogie/smoo/Checkouts/fathom",
        },
        "longname": "best#thing~yeah"
    }
    eq_(doclet_full_path(doclet, '/boogie/smoo/Checkouts'),
        ['./', 'fathom/', 'utils.', 'best#', 'thing~', 'yeah'])
