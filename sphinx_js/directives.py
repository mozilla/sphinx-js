from docutils.parsers.rst import Directive, Parser as RstParser
from docutils.parsers.rst.directives import flag
from sphinx.ext.autodoc import members_option

from .renderers import AutoFunctionRenderer, AutoClassRenderer, AutoAttributeRenderer


class JsDirective(Directive):
    """Abstract directive which knows how to pull things out of JSDoc output"""

    has_content = True
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = True

    option_spec = {
        'short-name': flag
    }


def auto_function_directive_bound_to_app(app):
    """Give the js:autofunction directive access to the Sphinx app singleton by
    closing over it.

    That's where we store the JSDoc output.

    """
    class AutoFunctionDirective(JsDirective):
        """js:autofunction directive, which spits out a js:function directive

        Takes a single argument which is a JS function name combined with an
        optional formal parameter list, all mashed together in a single string.

        """
        def run(self):
            return AutoFunctionRenderer(self, app).rst_nodes()

    return AutoFunctionDirective


def auto_class_directive_bound_to_app(app):
    """Give the js:autofunction directive access to the Sphinx app singleton by
    closing over it."""

    class AutoClassDirective(JsDirective):
        """js:autoclass directive, which spits out a js:class directive

        Takes a single argument which is a JS class name combined with an
        optional formal parameter list for the constructor, all mashed together
        in a single string.

        """
        option_spec = JsDirective.option_spec.copy()
        option_spec.update({
            'members': members_option,  # doesn't include constructor
            'exclude-members': _members_to_exclude,
            'private-members': flag})

        def run(self):
            return AutoClassRenderer(self, app).rst_nodes()

    return AutoClassDirective


def auto_attribute_directive_bound_to_app(app):
    """Give the js:autoattribute directive access to the Sphinx app singleton
    by closing over it."""

    class AutoAttributeDirective(JsDirective):
        """js:autoattribute directive, which spits out a js:attribute directive

        Takes a single argument which is a JS attribute name.

        """
        def run(self):
            return AutoAttributeRenderer(self, app).rst_nodes()

    return AutoAttributeDirective


def _members_to_exclude(arg):
    """Return a set of members to exclude given a comma-delim list them.

    Exclude none if none are passed. This differs from autodocs' behavior,
    which excludes all. That seemed useless to me.

    """
    return set(a.strip() for a in (arg or '').split(','))
