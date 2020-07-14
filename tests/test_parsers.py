# -*- coding: utf-8 -*-
from sphinx_js.parsers import PathVisitor


def test_escapes():
    r"""Make sure escapes work right and Python escapes like \n don't work."""
    assert PathVisitor().parse(r'd\.i:\nr/ut\\ils.max(whatever)') == [
        [r'd.i:nr/', r'ut\ils.', 'max'],
        '(whatever)',
    ]
