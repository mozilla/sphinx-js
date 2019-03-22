# -*- coding: utf-8 -*-
from nose.tools import assert_true

from tests.testing import SphinxBuildTestCase


class Tests(SphinxBuildTestCase):
    """Tests which require our one big Sphinx tree to be built (typescript version)"""

    def test_autoclass_constructor(self):
        """Make sure class constructor comes before methods."""
        contents = self._file_contents('index')
        pos_cstrct = contents.index('ClassDefinition constructor')
        pos_method = contents.index('ClassDefinition.method1')
        assert_true(pos_method > pos_cstrct, 'Constructor appears after method in ' + contents)

    def test_autoclass_order(self):
        """Make sure fields come before methods."""
        contents = self._file_contents('index')
        pos_field = contents.index('ClassDefinition.field')
        pos_method2 = contents.index('ClassDefinition.anotherMethod')
        pos_method = contents.index('ClassDefinition.method1')
        assert_true(pos_field < pos_method2 < pos_method, 'Methods and fields are not in right order in ' + contents)

    def test_autoclass_star_order(self):
        """Make sure fields come before methods even when using ``*``."""
        contents = self._file_contents('autoclass_star')
        pos_method = contents.index('ClassDefinition.method1')
        pos_field = contents.index('ClassDefinition.field')
        pos_method2 = contents.index('ClassDefinition.anotherMethod')
        assert_true(pos_method < pos_field < pos_method2, 'Methods and fields are not in right order in ' + contents)

    def test_generic_type(self):
        """Make sure all information about generic type is rendered"""
        contents = self._file_contents('index')
        assert_true(
            '**generic** (*Promise<Partial<class.ClassDefinition>>*)' in contents,
            'Generic type is rendered incompletely in ' + contents
        )
