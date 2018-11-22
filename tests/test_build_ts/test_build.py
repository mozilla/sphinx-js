# -*- coding: utf-8 -*-
from nose.tools import assert_true

from tests.testing import SphinxBuildTestCase


class Tests(SphinxBuildTestCase):
    """Tests which require our one big Sphinx tree to be built
    (typescript version)
    """

    def test_autoclass_constructor(self):
        """Make sure class constructor comes before methods."""
        contents = self._file_contents('index')
        pos_method = contents.index("ClassDefinition.method1")
        pos_cstrct = contents.index("ClassDefinition.new ClassDefinition")
        assert_true(pos_method > pos_cstrct, "Constructor appears after method in " + contents)
