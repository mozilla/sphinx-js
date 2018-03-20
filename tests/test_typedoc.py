from nose.tools import eq_
from sphinx_js.typedoc import Typedoc, parse_typedoc
from unittest import TestCase
from tempfile import mkdtemp
import os
import subprocess as sub
import shutil
import json

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
        
    def typedoc(self,source):
        outfile = os.path.join(self.tmpdir,source+'.json')
        sub.call([
            'typedoc.cmd', 
            '--out', self.tmpdir, 
            '--ignoreCompilerErrors', 
            '--json', outfile, 
            os.path.join(self.source_dir,source)
        ])
        return outfile

    # Running typedoc:
    #  typedoc --out TYPEDOC --json foo.json --ignoreCompilerErrors typescript/class.ts

    def test_empty(self):
        json={}
        jsdoc = Typedoc(json).jsdoc
        eq_(jsdoc,[])

    def test_references(self):
        for source in os.listdir(self.source_dir):
            if source.endswith(".ts"):
                with open(self.typedoc(source),"r") as typedocfile:
                    jsdoc = parse_typedoc(typedocfile)
                jsdoc_ref_file = os.path.join(self.source_dir,source+'.jsdoc')
                with open(jsdoc_ref_file,"r") as jsdocfile:
                    jsdoc_ref = json.load(jsdocfile)
                eq_(jsdoc,jsdoc_ref)