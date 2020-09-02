from os.path import join, normpath

from sphinx.errors import SphinxError

from .directives import (auto_class_directive_bound_to_app,
                         auto_function_directive_bound_to_app,
                         auto_attribute_directive_bound_to_app)
from .jsdoc import Analyzer as JsAnalyzer
from .typedoc import Analyzer as TsAnalyzer


def setup(app):
    # I believe this is the best place to run jsdoc. I was tempted to use
    # app.add_source_parser(), but I think the kind of source it's referring to
    # is RSTs.
    app.connect('builder-inited', analyze)

    app.connect('env-before-read-docs', read_all_docs)

    app.add_directive_to_domain('js',
                                'autofunction',
                                auto_function_directive_bound_to_app(app))
    app.add_directive_to_domain('js',
                                'autoclass',
                                auto_class_directive_bound_to_app(app))
    app.add_directive_to_domain('js',
                                'autoattribute',
                                auto_attribute_directive_bound_to_app(app))
    # TODO: We could add a js:module with app.add_directive_to_domain().

    app.add_config_value('js_language', 'javascript', 'env')
    app.add_config_value('js_source_path', '../', 'env')
    app.add_config_value('jsdoc_config_path', None, 'env')

    # We could use a callable as the "default" param here, but then we would
    # have had to duplicate or build framework around the logic that promotes
    # js_source_path to a list and calls abspath() on it. It's simpler this way
    # until we need to access js_source_path from more than one place.
    app.add_config_value('root_for_relative_js_paths', None, 'env')


def analyze(app):
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
        analyzer = {'javascript': JsAnalyzer,
                    'typescript': TsAnalyzer}[app.config.js_language]
    except KeyError:
        raise SphinxError('Unsupported value of js_language in config: %s' % app.config.js_language)

    # Analyze source code:
    app._sphinxjs_analyzer = analyzer.from_disk(abs_source_paths,
                                                app,
                                                root_for_relative_paths)


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


def read_all_docs(app, env, doc_names):
    """Add all found docs to the to-be-read list, because we have no way of
    telling which ones reference JS code that might have changed.

    Otherwise, builds go stale until you touch the stale RSTs or do a ``make
    clean``.

    """
    doc_names[:] = env.found_docs
