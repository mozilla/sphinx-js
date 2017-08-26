# -*- coding: utf-8 -*-
from io import open
from os.path import dirname, join
from shutil import rmtree
from unittest import TestCase

from nose.tools import eq_, ok_, assert_in, assert_not_in
from sphinx.cmdline import main as sphinx_main
from sphinx.util.osutil import cd


class Tests(TestCase):
    """Tests which require our one big Sphinx tree to be built.

    Yes, it's too coupled.

    """
    @classmethod
    def setup_class(cls):
        cls.docs_dir = join(dirname(__file__), 'source', 'docs')
        with cd(cls.docs_dir):
            if sphinx_main(['dummy', '-b', 'text', '-E', '.', '_build']):
                raise RuntimeError('Sphinx build exploded.')

    def _file_contents(self, filename):
        with open(join(self.docs_dir, '_build', '%s.txt' % filename),
                  encoding='utf8') as file:
            return file.read()

    def _file_contents_eq(self, filename, contents):
        eq_(self._file_contents(filename), contents)

    def test_autofunction_minimal(self):
        """Make sure we render correctly and pull the params out of the JS code
        when only the function name is provided."""
        self._file_contents_eq(
            'autofunction_minimal',
            'linkDensity(node)' + DESCRIPTION + FIELDS)

    def test_autofunction_explicit(self):
        """Make sure any explicitly provided params override the ones from the
        code, and make sure any explicit arbitrary RST content gets
        preserved."""
        self._file_contents_eq(
            'autofunction_explicit',
            'linkDensity(snorko, borko[, forko])' + DESCRIPTION + FIELDS + CONTENT)

    def test_autofunction_short(self):
        """Make sure the ``:short-name:`` option works."""
        self._file_contents_eq(
            'autofunction_short',
            'someMethod(hi)\n\n   Here.\n')

    def test_autofunction_long(self):
        """Make sure instance methods get converted to dotted notation which
        indexes better in Sphinx."""
        self._file_contents_eq(
            'autofunction_long',
            'ContainingClass.someMethod(hi)\n\n   Here.\n')

    def test_autoclass(self):
        """Make sure classes show their class comment and constructor
        comment."""
        contents = self._file_contents('autoclass')
        assert_in('Class doc.', contents)
        assert_in('Constructor doc.', contents)

    def test_autoclass_members(self):
        """Make sure classes list their members if ``:members:`` is specified.

        Make sure it shows both functions and attributes and shows getters and
        setters as if they are attributes. Make sure it doesn't show private
        members.

        """
        self._file_contents_eq(
            'autoclass_members',
            u'class ContainingClass(ho)\n\n   Class doc.\n\n   Constructor doc.\n\n   Arguments:\n      * **ho** – A thing\n\n   ContainingClass.bar\n\n      Setting this also frobs the frobnicator.\n\n   ContainingClass.someMethod(hi)\n\n      Here.\n\n   ContainingClass.someVar\n\n      A var\n')

    def test_autoclass_members_list(self):
        """Make sure including a list of names after ``members`` limits it to
        those names and follows the order you specify."""
        self._file_contents_eq(
            'autoclass_members_list',
            'class ClosedClass()\n\n   Closed class.\n\n   ClosedClass.publical3()\n\n      Public thing 3.\n\n   ClosedClass.publical()\n\n      Public thing.\n')

    def test_autoclass_alphabetical(self):
        """Make sure members sort alphabetically when not otherwise specified."""
        self._file_contents_eq(
            'autoclass_alphabetical',
            'class NonAlphabetical()\n\n   Non-alphabetical class.\n\n   NonAlphabetical.a()\n\n      Fun a.\n\n   NonAlphabetical.z()\n\n      Fun z.\n')

    def test_autoclass_private_members(self):
        """Make sure classes list their private members if
        ``:private-members:`` is specified."""
        contents = self._file_contents('autoclass_private_members')
        assert_in('secret()', contents)

    def test_autoclass_exclude_members(self):
        """Make sure ``exclude-members`` option actually excludes listed
        members."""
        contents = self._file_contents('autoclass_exclude_members')
        assert_in('publical()', contents)
        assert_not_in('publical2', contents)
        assert_not_in('publical3', contents)

    def test_autoattribute(self):
        """Make sure ``autoattribute`` works."""
        self._file_contents_eq(
            'autoattribute',
            'ContainingClass.someVar\n\n   A var\n')

    def test_getter_setter(self):
        """Make sure ES6-style getters and setters can be documented."""
        self._file_contents_eq(
            'getter_setter',
            'ContainingClass.bar\n\n   Setting this also frobs the frobnicator.\n')

    def test_no_shadowing(self):
        """Make sure we can disambiguate objects of the same name."""
        self._file_contents_eq(
            'avoid_shadowing',
            'more_code.shadow()\n\n   Another thing named shadow, to threaten to shadow the one in\n   code.js\n')

    def test_object_literal(self):
        """Make sure object initializer classes can be documented."""
        self._file_contents_eq(
            'autoclass_object_literal',
            'class ObjectLiteralClass()\n\n   Object initializer \u201cclass\u201d definition in literal notation.\n\n   ObjectLiteralClass.foo()\n\n      Foos the bars.\n\n      Arguments:\n         * **bar** (*string*) \u2013 the Bar to Foo.\n\n      Returns:\n         **string** \u2013 - Returns the Foo\u2019d Bar.\n')

    def test_private_forwarding(self):
        """Make sure public classes that forward to private classes can be documented."""
        self._file_contents_eq(
            'autoclass_private_forwarding',
            'class PublicClass()\n\n   This is the public API. All methods forward to PrivateClass.\n\n   PublicClass.public(foo)\n\n      This is the method we want to appear on the public API.\n\n      Arguments:\n         * **foo** (*string*) \u2013 We want the foo.\n')

    def test_autoclass_object_literal_private_forwarding(self):
        """Make sure public object initalizers that forward to private object initalizers can be documented."""
        self._file_contents_eq(
            'autoclass_object_literal_private_forwarding',
            'class PublicObjectLiteral()\n\n   This is the public API. All methods forward to PrivateClass.\n\n   PublicObjectLiteral.public()\n\n      This is the method we want to appear on the public API.\n\n      Arguments:\n         * **foo** (*string*) \u2013 We want the foo.\n')

    @classmethod
    def teardown_class(cls):
        rmtree(join(cls.docs_dir, '_build'))


DESCRIPTION = """

   Return the ratio of the inline text length of the links in an
   element to the inline text length of the entire element."""

FIELDS = u"""

   Arguments:
      * **node** (*Node*) – Something of a single type

   Throws:
      **PartyError|FartyError** – Something with multiple types and a
      line that wraps

   Returns:
      **Number** – What a thing
"""

# Oddly enough, the text renderer renders these bullets with a blank line
# between, but the HTML renderer does make them a single list.
CONTENT = """
   Things are "neat".

   Off the beat.

   * Sweet

   * Fleet
"""
