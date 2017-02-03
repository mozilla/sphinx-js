from .directive import auto_function_directive_bound_to_app
from .jsdoc import run_jsdoc


def setup(app):
    # I believe this is the best place to run jsdoc. I was tempted to use
    # app.add_source_parser(), but I think the kind of source it's referring to
    # is RSTs.
    app.connect('builder-inited', run_jsdoc)

    app.add_directive_to_domain('js',
                                'autofunction',
                                auto_function_directive_bound_to_app(app))
    # TODO: We could add a js:module with app.add_directive_to_domain().

    app.add_config_value('js_source_path', '../', 'env')
