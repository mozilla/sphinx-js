# -*- coding: utf-8 -*-
from nose.tools import assert_in, assert_not_in

from tests.testing import SphinxBuildTestCase


class Tests(SphinxBuildTestCase):
    """Tests which require our one big Sphinx tree to be built.

    Yes, it's too coupled.

    """
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

    def test_autofunction_typedef(self):
        """Make sure @typedef uses can be documented with autofunction."""
        self._file_contents_eq(
            'autofunction_typedef',
            u'TypeDefinition()\n\n   Arguments:\n      * **width** (*Number*) -- width in pixels\n')

    def test_autofunction_callback(self):
        """Make sure @callback uses can be documented with autofunction."""
        self._file_contents_eq(
            'autofunction_callback',
            u'requestCallback(responseCode)\n\n   Some global callback\n\n   Arguments:\n      * **responseCode** (*number*) --\n')

    def test_autofunction_example(self):
        """Make sure @example tags can be documented with autofunction."""
        self._file_contents_eq(
            'autofunction_example',
            u'exampleTag()\n\n'
            '   JSDoc example tag\n\n'
            '   **Examples:**\n\n'
            '      // This is the example.\n'
            '      exampleTag();\n')

    def test_autofunction_destructured_params(self):
        """Make sure that all documented params appears in the function
        definition."""
        self._file_contents_eq(
            'autofunction_destructured_params',
            u'destructuredParams(p1, p2)\n\n'
            '   Arguments:\n'
            '      * **p1** (*number*) --\n\n'
            '      * **p2** (*Object*) --\n\n'
            '      * **p2.foo** (*string*) --\n\n'
            '      * **p2.bar** (*string*) --\n')

    def test_autofunction_default_values(self):
        """Make sure params default values appear in the function definition,
        whether the defaults are defined in JSDoc or JS.

        Unfortunately, there is no way to disambiguate strings from symbolic
        values used as default args in JS code: for instance, ``true`` vs.
        ``"true"``. JSDoc's doclets render them both without quotes. However,
        you can work around this by specifying your defaults in the JSDoc
        comment rather than the JS code, as we do with p3. It would be lovely
        if JSDoc changed its behavior someday so we could know to put quotes
        around "foobar" as well.

        """
        self._file_contents_eq(
            'autofunction_default_values',
            u'defaultValues(p1=42, p2=foobar, p3="true")\n\n'
            '   Arguments:\n'
            '      * **p1** (*number*) --\n\n'
            '      * **p2** (*string*) --\n\n'
            '      * **p3** (*string*) --\n')

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
            u'class ContainingClass(ho)\n\n   Class doc.\n\n   Constructor doc.\n\n   Arguments:\n      * **ho** -- A thing\n\n   ContainingClass.anotherMethod()\n\n      Another.\n\n   ContainingClass.bar\n\n      Setting this also frobs the frobnicator.\n\n   ContainingClass.someMethod(hi)\n\n      Here.\n\n   ContainingClass.someVar\n\n      A var\n\n   ContainingClass.yetAnotherMethod()\n\n      More.\n')

    def test_autoclass_members_list(self):
        """Make sure including a list of names after ``members`` limits it to
        those names and follows the order you specify."""
        self._file_contents_eq(
            'autoclass_members_list',
            'class ClosedClass()\n\n   Closed class.\n\n   ClosedClass.publical3()\n\n      Public thing 3.\n\n   ClosedClass.publical()\n\n      Public thing.\n')

    def test_autoclass_members_list_star(self):
        """Make sure including ``*`` in a list of names after
        ``members`` includes the rest of the names in the normal order
        at that point."""
        self._file_contents_eq(
            'autoclass_members_list_star',
            u'class ContainingClass(ho)\n\n   Class doc.\n\n   Constructor doc.\n\n   Arguments:\n      * **ho** -- A thing\n\n   ContainingClass.bar\n\n      Setting this also frobs the frobnicator.\n\n   ContainingClass.anotherMethod()\n\n      Another.\n\n   ContainingClass.someVar\n\n      A var\n\n   ContainingClass.yetAnotherMethod()\n\n      More.\n\n   ContainingClass.someMethod(hi)\n\n      Here.\n')

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

    def test_autoclass_example(self):
        """Make sure @example tags can be documented with autoclass."""
        self._file_contents_eq(
            'autoclass_example',
            u'class ExampleClass()\n\n'
            '   JSDoc example tag for class\n\n'
            '   **Examples:**\n\n'
            '      // This is the example.\n'
            '      new ExampleClass();\n')

    def test_autoattribute(self):
        """Make sure ``autoattribute`` works."""
        self._file_contents_eq(
            'autoattribute',
            'ContainingClass.someVar\n\n   A var\n')

    def test_autoattribute_example(self):
        """Make sure @example tags can be documented with autoattribute."""
        self._file_contents_eq(
            'autoattribute_example',
            u'ExampleAttribute\n\n'
            '   JSDoc example tag for attribute\n\n'
            '   **Examples:**\n\n'
            '      // This is the example.\n'
            '      console.log(ExampleAttribute);\n')

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

    def test_restructuredtext_injection(self):
        """Make sure param names and types are escaped and cannot be
        interpreted as RestructuredText.
        """
        self._file_contents_eq(
            'injection',
            u'injection(a_, b)\n\n'
            '   Arguments:\n'
            '      * **a_** --\n\n'
            '      * **b** (*type_*) --\n\n'
            '   Returns:\n'
            '      **rtype_** --\n')


DESCRIPTION = """

   Return the ratio of the inline text length of the links in an
   element to the inline text length of the entire element."""

FIELDS = u"""

   Arguments:
      * **node** (*Node*) -- Something of a single type

   Throws:
      **PartyError|FartyError** -- Something with multiple types and a
      line that wraps

   Returns:
      **Number** -- What a thing
"""

# Oddly enough, the text renderer renders these bullets with a blank line
# between, but the HTML renderer does make them a single list.
CONTENT = """
   Things are "neat".

   Off the beat.

   * Sweet

   * Fleet
"""
