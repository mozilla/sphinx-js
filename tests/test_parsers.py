from nose.tools import eq_

from sphinx_js.parsers import PathVisitor


def test_escapes():
    r"""Make sure escapes work right and Python escapes like \n don't work."""
    eq_(PathVisitor().parse(r'd\.i:\nr/ut\\ils.max(whatever)'),
        [[r'd.i:nr/', 'ut\ils.', 'max'], '(whatever)'])
