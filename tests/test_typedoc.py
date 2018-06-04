import os
import subprocess as sub
import shutil
import json
from unittest import TestCase
from tempfile import mkdtemp

from nose.tools import eq_

from sphinx_js.typedoc import Typedoc, parse_typedoc


class Tests(TestCase):
    """Test typedoc to jsdoc conversion on typescript/*.ts
    """
    @classmethod
    def setup_class(cls):
        cls.source_dir = os.path.join(os.path.dirname(__file__), 'typescript')
        cls.tmpdir = mkdtemp()

    @classmethod
    def teardown_class(cls):
        shutil.rmtree(cls.tmpdir)

    def typedoc(self, source):
        outfile = os.path.join(self.tmpdir, source + '.json')
        typedoc_command_name = 'typedoc.cmd' if os.name == 'nt' else 'typedoc'

        sub.call([
            typedoc_command_name,
            '--out', self.tmpdir,
            '--ignoreCompilerErrors',
            '--json', outfile,
            os.path.join(self.source_dir, source)
        ])
        return outfile

    def test_empty(self):
        json = {}
        jsdoc = Typedoc(json).jsdoc
        eq_(jsdoc, [])

    def test_references(self):
        for source in os.listdir(self.source_dir):
            if source.endswith('.ts'):
                with open(self.typedoc(source), 'r') as typedocfile:
                    jsdoc = parse_typedoc(typedocfile)
                jsdoc_ref_file = os.path.join(self.source_dir, source + '.jsdoc')
                if not os.path.exists(jsdoc_ref_file):
                    with open(jsdoc_ref_file + '.ref', 'w') as jsdocfile:
                        json.dump(
                            jsdoc,
                            jsdocfile,
                            sort_keys=True,
                            indent=4,
                            separators=(',', ': '))
                    print('wrote %s' % jsdoc_ref_file)
                else:
                    with open(jsdoc_ref_file, 'r') as jsdocfile:
                        jsdoc_ref = json.load(jsdocfile)
                    eq_(jsdoc, jsdoc_ref)
