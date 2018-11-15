from codecs import getwriter
from collections import defaultdict
from errno import ENOENT
from json import load
import os
from os.path import abspath, relpath, splitext, sep
import subprocess
from tempfile import TemporaryFile, NamedTemporaryFile

from six import string_types
from sphinx.errors import SphinxError

from .parsers import path_and_formal_params, PathVisitor
from .suffix_tree import PathTaken, SuffixTree
from .typedoc import parse_typedoc


def gather_doclets(app):
    """Run JSDoc or another analysis tool across a whole codebase, and squirrel
    away its results in jsdoc doclet format."""
    source_paths = [app.config.js_source_path] if isinstance(app.config.js_source_path, string_types) else app.config.js_source_path
    # Uses cwd, which Sphinx seems to set to the dir containing conf.py:
    abs_source_paths = [abspath(path) for path in source_paths]

    root_for_relative_paths = root_or_fallback(app.config.root_for_relative_js_paths,
                                               abs_source_paths)

    analyze = analyzer_for(app.config.js_language)
    doclets = analyze(abs_source_paths, app)
    # 2 doclets are made for classes, and they are largely redundant: one for
    # the class itself and another for the constructor. However, the
    # constructor one gets merged into the class one and is intentionally
    # marked as undocumented, even if it isn't. See
    # https://github.com/jsdoc3/jsdoc/issues/1129.
    doclets = [d for d in doclets if d.get('comment')
                                     and not d.get('undocumented')]

    # Build table for lookup by name, which most directives use:
    app._sphinxjs_doclets_by_path = SuffixTree()
    conflicts = []
    for d in doclets:
        try:
            app._sphinxjs_doclets_by_path.add(
                doclet_full_path(d, root_for_relative_paths),
                d)
        except PathTaken as conflict:
            conflicts.append(conflict.segments)
    if conflicts:
        raise PathsTaken(conflicts)

    # Build lookup table for autoclass's :members: option. This will also
    # pick up members of functions (inner variables), but it will instantly
    # filter almost all of them back out again because they're undocumented.
    # We index these by unambiguous full path. Then, when looking them up by
    # arbitrary name segment, we disambiguate that first by running it through
    # the suffix tree above. Expect trouble due to jsdoc's habit of calling
    # things (like ES6 class methods) "<anonymous>" in the memberof field, even
    # though they have names. This will lead to multiple methods having each
    # other's members. But if you don't have same-named inner functions or
    # inner variables that are documented, you shouldn't have trouble.
    app._sphinxjs_doclets_by_class = defaultdict(lambda: [])
    for d in doclets:
        of = d.get('memberof')
        if of:  # speed optimization
            segments = doclet_full_path(d, root_for_relative_paths, longname_field='memberof')
            app._sphinxjs_doclets_by_class[tuple(segments)].append(d)


def program_name_on_this_platform(program):
    """Return the name of the executable file on the current platform, given a
    command name with no extension."""
    return program + '.cmd' if os.name == 'nt' else program


class Command(object):
    def __init__(self, program):
        self.program = program_name_on_this_platform(program)
        self.args = []

    def add(self, *args):
        self.args.extend(args)

    def make(self):
        return [self.program] + self.args


def analyze_jsdoc(abs_source_paths, app):
    command = Command('jsdoc')
    command.add('-X', *abs_source_paths)
    if app.config.jsdoc_config_path:
        command.add('-c', app.config.jsdoc_config_path)

    # Use a temporary file to handle large output volume. JSDoc defaults to
    # utf8-encoded output.
    with getwriter('utf-8')(TemporaryFile(mode='w+b')) as temp:
        try:
            p = subprocess.Popen(command.make(), cwd=app.confdir, stdout=temp)
        except OSError as exc:
            if exc.errno == ENOENT:
                raise SphinxError('%s was not found. Install it using "npm install -g jsdoc".' % command.program)
            else:
                raise
        p.wait()
        # Once output is finished, move back to beginning of file and load it:
        temp.seek(0)
        try:
            return load(temp)
        except ValueError:
            raise SphinxError('jsdoc found no JS files in the directories %s. Make sure js_source_path is set correctly in conf.py. It is also possible (though unlikely) that jsdoc emitted invalid JSON.' % abs_source_paths)


def analyze_typescript(abs_source_paths, app):
    command = Command('typedoc')
    if app.config.jsdoc_config_path:
        command.add('--tsconfig', app.config.jsdoc_config_path)

    with getwriter('utf-8')(NamedTemporaryFile(mode='w+b')) as temp:
        command.add('--json', temp.name, *abs_source_paths)
        try:
            subprocess.call(command.make())
        except OSError as exc:
            if exc.errno == ENOENT:
                raise SphinxError('%s was not found. Install it using "npm install -g typedoc".' % command.program)
            else:
                raise
        # typedoc emits a valid JSON file even if it finds no TS files in the dir:
        return parse_typedoc(temp)


ANALYZERS = {'javascript': analyze_jsdoc,
             'typescript': analyze_typescript}


def analyzer_for(language):
    """Return a callable that spits out JSDoc-style doclets from some language:
    JS, TypeScript, or other."""
    try:
        return ANALYZERS[language]
    except KeyError:
        raise SphinxError('Unsupported value of js_language in config: %s' % language)


def root_or_fallback(root_for_relative_paths, abs_source_paths):
    """Return the path that relative JS entity paths in the docs are relative to.

    Fall back to the sole JS source path if the setting is unspecified.

    :arg root_for_relative_paths: The raw root_for_relative_js_paths setting.
        None if the user hasn't specified it.
    :arg abs_source_paths: Absolute paths of dirs to scan for JS code

    """
    if root_for_relative_paths:
        return abspath(root_for_relative_paths)
    else:
        if len(abs_source_paths) > 1:
            raise SphinxError('Since more than one js_source_path is specified in conf.py, root_for_relative_js_paths must also be specified. This allows paths beginning with ./ or ../ to be unambiguous.')
        else:
            return abs_source_paths[0]


def doclet_full_path(d, base_dir, longname_field='longname'):
    """Return the full, unambiguous list of path segments that points to an
    entity described by a doclet.

    Example: ``['./', 'dir/', 'dir/', 'file/', 'object.', 'object#', 'object']``

    :arg d: The doclet
    :arg base_dir: Absolutized value of the jsdoc_source_path option
    :arg longname_field: The field to look in at the top level of the doclet
        for the long name of the object to emit a path to
    """
    meta = d['meta']
    rel = relpath(meta['path'], base_dir)
    rel = '/'.join(rel.split(sep))
    if not rel.startswith(('../', './')) and rel not in ('..', '.'):
        # It just starts right out with the name of a folder in the cwd.
        rooted_rel = './%s' % rel
    else:
        rooted_rel = rel

    # Building up a string and then parsing it back down again is probably
    # not the fastest approach, but it means knowledge of path format is in
    # one place: the parser.
    path = '%s/%s.%s' % (rooted_rel,
                         splitext(meta['filename'])[0],
                         d[longname_field])
    return PathVisitor().visit(
        path_and_formal_params['path'].parse(path))


class PathsTaken(Exception):
    """One or more JS objects had the same paths.

    Rolls up multiple PathTaken exceptions for mass reporting.

    """
    def __init__(self, conflicts):
        # List of paths, each given as a list of segments:
        self.conflicts = conflicts

    def __str__(self):
        return ('Your JS code contains multiple documented objects at each of '
                "these paths:\n\n  %s\n\nWe won't know which one you're "
                'talking about. Using JSDoc tags like @class might help you '
                'differentiate them.' %
                '\n  '.join(''.join(c) for c in self.conflicts))
