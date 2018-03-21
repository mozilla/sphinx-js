from os.path import dirname, join
from shutil import rmtree
from unittest import TestCase
import sys

from sphinx.cmdline import main as sphinx_main
from sphinx.util.osutil import cd


class SphinxBuildTestCase(TestCase):
    """Base class for tests which require a Sphinx tree to be built and then
    deleted afterward

    """
    @classmethod
    def setup_class(cls):
        """Run Sphinx against the dir adjacent to the testcase."""
        cls.docs_dir = join(cls.this_dir(), 'source', 'docs')
        with cd(cls.docs_dir):
            if sphinx_main(['.', '-b', 'text', '-E', '_build']):
                raise RuntimeError('Sphinx build exploded.')

    @classmethod
    def teardown_class(cls):
        rmtree(join(cls.docs_dir, '_build'))

    @classmethod
    def this_dir(cls):
        """Return the path to the dir containing the testcase class."""
        # nose does some amazing magic that makes this work even if there are
        # multiple test modules with the same name:
        return dirname(sys.modules[cls.__module__].__file__)
