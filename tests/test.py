from os.path import dirname, join
from shutil import rmtree
from unittest import TestCase

from nose.tools import eq_
from sphinx.cmdline import main as sphinx_main
from sphinx.util.osutil import cd


class AutoFunctionTests(TestCase):
    """Tests for the ``js-autofunction`` directive"""

    @classmethod
    def setup_class(cls):
        cls.docs_dir = join(dirname(__file__), 'source', 'docs')
        with cd(cls.docs_dir):
            sphinx_main(['dummy', '-b', 'text', '-E', '.', '_build'])

    def _file_contents_eq(self, filename, contents):
        with open(join(self.docs_dir, '_build', '%s.txt' % filename)) as file:
            eq_(file.read(), contents)

    def test_autofunction_minimal(self):
        self._file_contents_eq('index',
"""linkDensity(node)

   Return the ratio of the inline text length of the links in an
   element to the inline text length of the entire element.
""")

    def test_autofunction_explicit(self):
        self._file_contents_eq('explicit',
"""linkDensity(snorko, borko[, forko])

   Return the ratio of the inline text length of the links in an
   element to the inline text length of the entire element.
""")

    @classmethod
    def teardown_class(cls):
        rmtree(join(cls.docs_dir, '_build'))


# test_content """Make sure literal content is preserved."""
# test_explicit_args """Make sure you're allowed to write out the args explicitly."""