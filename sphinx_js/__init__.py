from .directive import (auto_class_directive_bound_to_app,
                        auto_function_directive_bound_to_app,
                        auto_attribute_directive_bound_to_app)
from .jsdoc import run_jsdoc


def setup(app):
    # I believe this is the best place to run jsdoc. I was tempted to use
    # app.add_source_parser(), but I think the kind of source it's referring to
    # is RSTs.
    app.connect('builder-inited', run_jsdoc)

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

    app.add_config_value('js_source_path', '../', 'env')
    app.add_config_value('jsdoc_config_path', None, 'env')


def read_all_docs(app, env, doc_names):
    """Add all found docs to the to-be-read list, because we have no way of
    telling which ones reference JS code that might have changed.

    Otherwise, builds go stale until you touch the stale RSTs or do a ``make
    clean``.

    """
    doc_names[:] = env.found_docs
