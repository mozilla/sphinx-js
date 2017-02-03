from os.path import dirname, join
from shutil import rmtree
from unittest import TestCase

from nose.tools import eq_
from sphinx.cmdline import main as sphinx_main
from sphinx.util.osutil import cd


class AutoFunctionTests(TestCase):
    """Tests for the ``js:autofunction`` directive"""

    @classmethod
    def setup_class(cls):
        cls.docs_dir = join(dirname(__file__), 'source', 'docs')
        with cd(cls.docs_dir):
            sphinx_main(['dummy', '-b', 'text', '-E', '.', '_build'])

    def _file_contents_eq(self, filename, contents):
        with open(join(self.docs_dir, '_build', '%s.txt' % filename)) as file:
            eq_(file.read(), contents)

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

    @classmethod
    def teardown_class(cls):
        rmtree(join(cls.docs_dir, '_build'))


DESCRIPTION = """

   Return the ratio of the inline text length of the links in an
   element to the inline text length of the entire element."""

FIELDS = """

   Throws:
      **PartyError|FartyError** -- Something with multiple types

   Returns:
      **Number** -- What a thing

   Arguments:
      * **node** (*Node*) -- Something of a single type
"""

# Oddly enough, the text renderer renders these bullets with a blank line
# between, but the HTML renderer does make them a single list.
CONTENT = """
   Things are "neat".

   Off the beat.

   * Sweet

   * Fleet
"""
