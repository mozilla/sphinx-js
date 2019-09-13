# -*- coding: utf-8 -*-
import os
import subprocess
import shutil
import json
from tempfile import mkdtemp

import pytest

from sphinx_js.doclets import program_name_on_this_platform
from sphinx_js.typedoc import TypeDoc, parse_typedoc

TS_SOURCE_DIR = os.path.join(os.path.dirname(__file__), 'typescript')
TS_FILE_LIST = list(filter(lambda x: x.endswith('.ts'), os.listdir(TS_SOURCE_DIR)))


@pytest.fixture(scope='module')
def typedoc():
    tmpdir = mkdtemp()

    def inner_func(source):
        outfile = os.path.join(tmpdir, source + '.json')
        typedoc_command_name = program_name_on_this_platform('typedoc')

        subprocess.call([
            typedoc_command_name,
            '--out', tmpdir,
            '--ignoreCompilerErrors',
            '--target', 'ES6',
            '--json', outfile,
            os.path.join(TS_SOURCE_DIR, source)
        ])
        return outfile
    yield inner_func
    shutil.rmtree(tmpdir)


@pytest.fixture(params=TS_FILE_LIST)
def references(request, typedoc):
    source = request.param
    with open(typedoc(source), 'r') as typedocfile:
        jsdoc = parse_typedoc(typedocfile)
    jsdoc_ref_file = os.path.join(TS_SOURCE_DIR, source + '.jsdoc')
    if not os.path.exists(jsdoc_ref_file):
        # When a reference file is missing, this is probably a new test.
        # Generate a reference file for the developer to review.  If the
        # generated reference is good, just remove the '.ref' extension.
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
        return {'jsdoc': jsdoc, 'jsdoc_ref': jsdoc_ref}


def test_empty():
    json = {}
    jsdoc = TypeDoc(json).jsdoc
    assert jsdoc == []


def test_references(references):
    assert references['jsdoc'] == references['jsdoc_ref']
