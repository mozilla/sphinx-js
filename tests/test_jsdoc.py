from nose.tools import eq_

from sphinx_js.jsdoc import doclet_full_path


def test_doclet_full_path():
    doclet = {
        "meta": {
            "filename": "utils.js",
            "path": "/boogie/smoo/Checkouts/fathom",
        },
        "longname": "best#thing~yeah"
    }
    eq_(doclet_full_path(doclet, '/boogie/smoo/Checkouts'),
        ['./', 'fathom/', 'utils.', 'best#', 'thing~', 'yeah'])
