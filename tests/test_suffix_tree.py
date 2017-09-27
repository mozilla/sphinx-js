from nose.tools import assert_raises, eq_

from sphinx_js.suffix_tree import SuffixAmbiguous, SuffixNotFound, SuffixTree


def test_things():
    s = SuffixTree()
    s.add(['./', 'dir/', 'utils.', 'max'], 1)
    s.add(['./', 'dir/', 'footils.', 'max'], 2)
    s.add(['./', 'dir/', 'footils.', 'hacks'], 3)

    eq_(s.get(['hacks']), 3)
    eq_(s.get(['footils.', 'max']), 2)
    assert_raises(SuffixNotFound, s.get, ['quacks.', 'max'])
    assert_raises(SuffixAmbiguous, s.get, ['max'])
