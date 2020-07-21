# TODO: Maybe move this whole file into __init__.
from codecs import getreader
from errno import ENOENT
from os.path import join, normpath
import subprocess
from tempfile import NamedTemporaryFile

from sphinx.errors import SphinxError

from .typedoc import parse_typedoc


def gather_doclets(app):
    """Run JSDoc or another analysis tool across a whole codebase, and squirrel
    away its results in a language-specific Analyzer."""
    # Normalize config values:
    source_paths = [app.config.js_source_path] if isinstance(app.config.js_source_path, str) else app.config.js_source_path
    abs_source_paths = [normpath(join(app.confdir, path)) for path in source_paths]
    root_for_relative_paths = root_or_fallback(
        normpath(join(app.confdir, app.config.root_for_relative_js_paths)) if app.config.root_for_relative_js_paths else None,
        abs_source_paths)

    # Pick analyzer:
    try:
        analyzer = {'javascript': javascript.Analyzer,
                    'typescript': typescript.Analyzer}[app.config.js_language]
    except KeyError:
        raise SphinxError('Unsupported value of js_language in config: %s' % language)

    # Analyze source code:
    app._sphinxjs_analyzer = analyzer.from_disk(abs_source_paths,
                                                app,
                                                root_for_relative_paths)


def analyze_typescript(abs_source_paths, app):
    command = Command('typedoc')
    if app.config.jsdoc_config_path:
        command.add('--tsconfig', normpath(join(app.confdir, app.config.jsdoc_config_path)))

    with NamedTemporaryFile(mode='w+b') as temp:
        command.add('--json', temp.name, *abs_source_paths)
        try:
            subprocess.call(command.make())
        except OSError as exc:
            if exc.errno == ENOENT:
                raise SphinxError('%s was not found. Install it using "npm install -g typedoc".' % command.program)
            else:
                raise
        # typedoc emits a valid JSON file even if it finds no TS files in the dir:
        return parse_typedoc(getreader('utf-8')(temp))


def root_or_fallback(root_for_relative_paths, abs_source_paths):
    """Return the path that relative JS entity paths in the docs are relative to.

    Fall back to the sole JS source path if the setting is unspecified.

    :arg root_for_relative_paths: The absolute-ized root_for_relative_js_paths
        setting. None if the user hasn't specified it.
    :arg abs_source_paths: Absolute paths of dirs to scan for JS code

    """
    if root_for_relative_paths:
        return root_for_relative_paths
    else:
        if len(abs_source_paths) > 1:
            raise SphinxError('Since more than one js_source_path is specified in conf.py, root_for_relative_js_paths must also be specified. This allows paths beginning with ./ or ../ to be unambiguous.')
        else:
            return abs_source_paths[0]
