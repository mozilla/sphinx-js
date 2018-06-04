from codecs import getwriter
from errno import ENOENT
import subprocess
import os
from os.path import abspath
from tempfile import TemporaryFile, NamedTemporaryFile
from json import load

from six import string_types
from sphinx.errors import SphinxError
from sphinx.util.logging import getLogger

from .typedoc import parse_typedoc

logger = getLogger(__name__)


class Command(object):
    def __init__(self, program):
        self.program = program + '.cmd' if os.name == 'nt' else program
        self.args = []

    def add(self, *args):
        self.args.extend(args)

    def make(self):
        command = [self.program]
        command.extend(self.args)
        logger.info('running: ' + ' '.join(command))
        return command


def absolute_source_paths(app):
        source_paths = [app.config.js_source_path] if isinstance(app.config.js_source_path, string_types) else app.config.js_source_path
        # Uses cwd, which Sphinx seems to set to the dir containing conf.py:
        return [abspath(path) for path in source_paths]


def jsdoc_generator(app):
    abs_source_paths = absolute_source_paths(app)
    jsdoc_command = Command('jsdoc')
    jsdoc_command.add(*abs_source_paths)
    jsdoc_command.add('-X')
    if app.config.jsdoc_config_path:
        jsdoc_command.add('-c', app.config.jsdoc_config_path)

    # Use a temporary file to handle large output volume. JSDoc defaults to
    # utf8-encoded output.
    with getwriter('utf-8')(TemporaryFile(mode='w+')) as temp:
        try:
            p = subprocess.Popen(jsdoc_command.make(), stdout=temp)
        except OSError as exc:
            if exc.errno == ENOENT:
                raise SphinxError('%s was not found. Install it using "npm install -g jsdoc".' % jsdoc_command.program)
            else:
                raise
        p.wait()
        # Once output is finished, move back to beginning of file and load it:
        temp.seek(0)
        try:
            return load(temp)
        except ValueError:
            raise SphinxError('jsdoc found no JS files in the directories %s. Make sure js_source_path is set correctly in conf.py. It is also possible (though unlikely) that jsdoc emitted invalid JSON.' % abs_source_paths)


def typedoc_generator(app):
    abs_source_paths = absolute_source_paths(app)
    with getwriter('utf-8')(NamedTemporaryFile(mode='w+')) as temp:
        jsdoc_command = Command('typedoc')
        jsdoc_command.add('--json', temp.name)
        jsdoc_command.add(*abs_source_paths)
        if app.config.jsdoc_config_path:
            jsdoc_command.add('--tsconfig', app.config.jsdoc_config_path)
        try:
            subprocess.call(jsdoc_command.make())
        except OSError as exc:
            if exc.errno == ENOENT:
                raise SphinxError('%s was not found. Install it using "npm install -g typedoc".' % jsdoc_command.program)
            else:
                raise

        try:
            return parse_typedoc(temp)
        except ValueError:
            raise SphinxError('typedoc found no TS files in the directories %s. Make sure js_source_path is set correctly in conf.py. It is also possible (though unlikely) that typedoc emitted invalid JSON.' % abs_source_paths)


def generate_doclets(app):
    if app.config.js_language == 'javascript':
        return jsdoc_generator(app)

    elif app.config.js_language == 'typescript':
        return typedoc_generator(app)

    else:
        raise SphinxError('unknown JS language: ' + app.config.js_language)
