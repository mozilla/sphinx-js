from os.path import join
from shutil import rmtree
from tempfile import mkdtemp
from textwrap import dedent
from unittest import TestCase

from nose.tools import eq_
from sphinx.application import Sphinx


class FakeSphinx(Sphinx):
    """Fake Sphinx app that has better defaults"""
    def __init__(self, tmpdir):
        srcdir = tmpdir
        confdir = tmpdir
        outdir = join(tmpdir, '_build', 'text')
        doctreedir = join(tmpdir, 'doctree')

        with open(join(confdir, 'conf.py'), 'w') as fp:
            fp.write('master_doc = "index"')

        super(FakeSphinx, self).__init__(
            srcdir=srcdir,
            confdir=confdir,
            outdir=outdir,
            doctreedir=doctreedir,
            buildername='text',
            freshenv=True,
        )


def parse(tmpdir, text):
    fakesphinx = FakeSphinx(tmpdir)
    fakesphinx.setup_extension('sphinx_js')

    text = 'BEGINBEGIN\n\n%s\n\nENDEND' % text

    with open(join(tmpdir, 'index.rst'), 'w') as fp:
        fp.write(text)

    fakesphinx.builder.build_all()

    with open(join(tmpdir, '_build/text/index.txt'), 'r') as fp:
        data = fp.read()

    # index.text has a bunch of stuff in it. BEGINBEGIN and ENDEND are markers,
    # so we just return the bits in between.
    data = data[data.find('BEGINBEGIN') + 10:data.find('ENDEND')]
    # Strip the whitespace, but add a \n to make tests easier to read.
    data = data.strip() + '\n'
    return data


class TempDirTests(TestCase):
    def setUp(self):
        self.tmpdir = mkdtemp()

    def test_tests(self):
        """Verify test harness is working."""
        eq_(parse(self.tmpdir, '*foo*'),
            dedent('''\
            *foo*
            '''))

    def test_defaults(self):
        rst = dedent('''\
        .. autoconfig:: test_autoconfig.ComponentDefaults
        ''')

        eq_(parse(self.tmpdir, rst),
            dedent('''\
            Hello, Dolly!
            '''))

    def tearDown(self):
        rmtree(self.tmpdir)
