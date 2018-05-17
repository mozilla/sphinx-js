from codecs import getwriter
from errno import ENOENT
import subprocess
import os
from os.path import abspath
from tempfile import TemporaryFile, NamedTemporaryFile
from json import load
from sphinx.errors import SphinxError
from sphinx.util.logging import getLogger
from six import string_types
from .typedoc import parse_typedoc

logger = getLogger(__name__)


class Command(object):
    def __init__(self, program):
        self.program = program+".cmd" if os.name == 'nt' else program
        self.args = []

    def add(self, *args):
        self.args.extend(args)

    def make(self):
        command = [self.program]
        command.extend(self.args)
        logger.info('running: ' + ' '.join(command))
        return command


class Generator(object):
    def __init__(self, app):
        self.app = app
        source_paths = [app.config.js_source_path] if isinstance(app.config.js_source_path, string_types) else app.config.js_source_path
        # Uses cwd, which Sphinx seems to set to the dir containing conf.py:
        self.abs_source_paths = [abspath(path) for path in source_paths]


class JSDocGenerator(Generator):
    def run(self):
        jsdoc_command = Command('jsdoc')
        jsdoc_command.add(*self.abs_source_paths)
        jsdoc_command.add('-X')
        if self.app.config.jsdoc_config_path:
            jsdoc_command.add('-c', self.app.config.jsdoc_config_path)

        # Use a temporary file to handle large output volume. JSDoc defaults to
        # utf8-encoded output.
        with getwriter('utf-8')(TemporaryFile(mode='w+')) as temp:
            try:
                p = subprocess.Popen(jsdoc_command.make(), stdout=temp)
            except OSError as exc:
                if exc.errno == ENOENT:
                    raise SphinxError('%s was not found. Install it using "npm install -g jsdoc".' % jsdoc_command_name)
                else:
                    raise
            p.wait()
            # Once output is finished, move back to beginning of file and load it:
            temp.seek(0)
            try:
                return load(temp)
            except ValueError:
                raise SphinxError('jsdoc found no JS files in the directories %s. Make sure js_source_path is set correctly in conf.py. It is also possible (though unlikely) that jsdoc emitted invalid JSON.' % self.abs_source_paths)


class TypedocGenerator(Generator):
    def run(self):
        with getwriter('utf-8')(NamedTemporaryFile(mode='w+')) as temp:
            jsdoc_command = Command('typedoc')
            jsdoc_command.add('--json', temp.name)
            jsdoc_command.add(*self.abs_source_paths)
<<<<<<< eeacb9237af86b8b6e6dfd960f4696ab43e91aec
            if self.app.config.jsdoc_config_path:
                jsdoc_command.add('--tsconfig', self.app.config.jsdoc_config_path)
=======
>>>>>>> Refactor jsdoc.py
            subprocess.call(jsdoc_command.make())

            try:
                return parse_typedoc(temp)
            except ValueError:
                raise SphinxError('typedoc found no TS files in the directories %s. Make sure js_source_path is set correctly in conf.py. It is also possible (though unlikely) that typedoc emitted invalid JSON.' % self.abs_source_paths)


def generate_doclets(app):
    if app.config.js_language == 'javascript':
        return JSDocGenerator(app).run()

    elif app.config.js_language == 'typescript':
        return TypedocGenerator(app).run()

    else:
        raise SphinxError('unknown JS language: ' + app.config.js_language)
