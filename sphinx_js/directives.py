"""These are the actual Sphinx directives we provide, but they are skeletal.

The real meat is in their parallel renderer classes, in renderers.py. The split
is due to the unfortunate trick we need here of having functions return the
directive classes after providing them the ``app`` symbol, where we store the
JSDoc output, via closure. The renderer classes, able to be top-level classes,
can access each other and collaborate.

"""
from os.path import join, relpath

from docutils.parsers.rst import Directive
from docutils.parsers.rst.directives import flag
from sphinx import addnodes
from sphinx.domains.javascript import JSCallable

from .renderers import (AutoFunctionRenderer,
                        AutoClassRenderer,
                        AutoAttributeRenderer)


class JsDirective(Directive):
    """Abstract directive which knows how to pull things out of our IR"""

    has_content = True
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = True

    option_spec = {
        'short-name': flag
    }


def note_dependencies(app, dependencies):
    """Note dependencies of current document.

    :arg app: Sphinx application object
    :arg dependencies: iterable of filename strings relative to root_for_relative_paths
    """
    for fn in dependencies:
        # Dependencies in the IR are relative to `root_for_relative_paths`, itself
        # relative to the configuration directory.
        abs = join(app._sphinxjs_analyzer._base_dir, fn)
        # Sphinx dependencies are relative to the source directory.
        rel = relpath(abs, app.srcdir)
        app.env.note_dependency(rel)


def auto_function_directive_bound_to_app(app):
    class AutoFunctionDirective(JsDirective):
        """js:autofunction directive, which spits out a js:function directive

        Takes a single argument which is a JS function name combined with an
        optional formal parameter list, all mashed together in a single string.

        """
        def run(self):
            renderer = AutoFunctionRenderer.from_directive(self, app)
            note_dependencies(app, renderer.dependencies())
            return renderer.rst_nodes()

    return AutoFunctionDirective


def auto_class_directive_bound_to_app(app):
    class AutoClassDirective(JsDirective):
        """js:autoclass directive, which spits out a js:class directive

        Takes a single argument which is a JS class name combined with an
        optional formal parameter list for the constructor, all mashed together
        in a single string.

        """
        option_spec = JsDirective.option_spec.copy()
        option_spec.update({
            'members': lambda members: ([m.strip() for m in members.split(',')]
                                        if members else []),
            'exclude-members': _members_to_exclude,
            'private-members': flag})

        def run(self):
            renderer = AutoClassRenderer.from_directive(self, app)
            note_dependencies(app, renderer.dependencies())
            return renderer.rst_nodes()

    return AutoClassDirective


def auto_attribute_directive_bound_to_app(app):
    class AutoAttributeDirective(JsDirective):
        """js:autoattribute directive, which spits out a js:attribute directive

        Takes a single argument which is a JS attribute name.

        """
        def run(self):
            renderer = AutoAttributeRenderer.from_directive(self, app)
            note_dependencies(app, renderer.dependencies())
            return renderer.rst_nodes()

    return AutoAttributeDirective


def _members_to_exclude(arg):
    """Return a set of members to exclude given a comma-delim list them.

    Exclude none if none are passed. This differs from autodocs' behavior,
    which excludes all. That seemed useless to me.

    """
    return set(a.strip() for a in (arg or '').split(','))


class JSStaticFunction(JSCallable):
    """Like a callable but with a different prefix."""
    def get_display_prefix(self):
        return [addnodes.desc_sig_keyword('static', 'static'),
                addnodes.desc_sig_space()]
