# -*- coding: utf-8 -*-
from tests.testing import SphinxBuildTestCase


class TextBuilderTests(SphinxBuildTestCase):
    """Tests which require our one big Sphinx tree to be built (as text)"""

    def test_autoclass_constructor(self):
        """Make sure class constructor comes before methods."""
        contents = self._file_contents('index')
        pos_cstrct = contents.index('ClassDefinition constructor')
        pos_method = contents.index('ClassDefinition.method1')
        assert pos_method > pos_cstrct, 'Constructor appears after method in ' + contents

    def test_autoclass_order(self):
        """Make sure fields come before methods."""
        contents = self._file_contents('index')
        pos_field = contents.index('ClassDefinition.field')
        pos_method2 = contents.index('ClassDefinition.anotherMethod')
        pos_method = contents.index('ClassDefinition.method1')
        assert pos_field < pos_method2 < pos_method, 'Methods and fields are not in right order in ' + contents

    def test_autoclass_star_order(self):
        """Make sure fields come before methods even when using ``*``."""
        contents = self._file_contents('autoclass_star')
        pos_method = contents.index('ClassDefinition.method1')
        pos_field = contents.index('ClassDefinition.field')
        pos_method2 = contents.index('ClassDefinition.anotherMethod')
        assert pos_method < pos_field < pos_method2, 'Methods and fields are not in right order in ' + contents

    def test_abstract_extends_and_implements(self):
        """Make sure the template correctly represents abstract classes,
        classes with superclasses, and classes that implement interfaces.

        These are all TypeScript-specific features.

        """
        # The quotes around ClassDefinition() must be some weird decision in
        # Sphinx's templates. I don't care if they go away in a future version
        # of Sphinx.
        self._file_contents_eq(
            'autoclass_class_with_interface_and_supers',
            'class ClassWithSupersAndInterfacesAndAbstract()\n'
            '\n'
            '   *abstract*\n'
            '\n'
            '   **Extends:**\n'
            '      * "ClassDefinition()"\n'
            '\n'
            '   I construct.\n')
            # TODO: Add interfaces.


class HtmlBuilderTests(SphinxBuildTestCase):
    """Tests which require an HTML build of our Sphinx tree, for checking
    links"""

    builder = 'html'

    def test_extends_links(self):
        """Make sure superclass mentions link to their definitions."""
        assert 'href="index.html#class.ClassDefinition"' in self._file_contents('autoclass_class_with_interface_and_supers')
