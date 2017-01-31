from os.path import dirname, join
from shutil import rmtree
from subprocess import check_call
from unittest import TestCase

from nose.tools import eq_
from sphinx.util.osutil import cd


class Tests(TestCase):
    def setUp(self):
        self.docs_dir = join(dirname(__file__), 'source', 'docs')
        with cd(self.docs_dir):
            check_call(['sphinx-build', '-b', 'text', '-E', '.', '_build'])

    def _file_contents_eq(self, filename, contents):
        with open(join(self.docs_dir, '_build', '%s.txt' % filename)) as file:
            eq_(file.read(), contents)

    def test_autofunction(self):
        self._file_contents_eq('index', 'Return the ratio of the inline text length of the links in an element\nto the inline text length of the entire element.\n')

    def tearDown(self):
        rmtree(join(self.docs_dir, '_build'))
