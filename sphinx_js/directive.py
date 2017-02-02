from os.path import dirname, join

from docutils.parsers.rst import Directive, Parser as RstParser
from docutils.utils import new_document
from jinja2 import Environment, FileSystemLoader


def auto_function_directive_bound_to_app(app):
    """Give the js-autofunction directive access to the Sphinx app singleton by
    closing over it.

    That's where we store the JSDoc output.

    """
    class AutoFunctionDirective(Directive):
        """js-autofunction directive, which spits out a js:function directive

        Takes a single argument which is a JS function name combined with an
        optional formal parameter list, all mashed together in a single string.

        """
        has_content = True
        required_arguments = 1
        optional_arguments = 0
        final_argument_whitespace = True

        option_spec = {}

        def run(self):
            # Get the relevant documentation together:
            name = self._function_name()
            doclet = app._sphinxjs_jsdoc_output[name]
            params = self._function_params(doclet)

            # Render to RST using Jinja:
            env = Environment(loader=FileSystemLoader(join(dirname(__file__), 'templates')))
            template = env.get_template('function.rst')
            rst = template.render(
                name=name,
                params=params,
                description=doclet.get('description', ''))

            # Parse the RST into docutils nodes with a fresh doc, and return
            # them:
            #
            # Not sure if passing the settings from the "real" doc is the right
            # thing to do here:
            doc = new_document('dummy', settings=self.state.document.settings)
            RstParser().parse(rst, doc)
            return doc.children

        def _function_params(self, doclet):
            """Return the JS function params, looking first to any explicit
            params written into the directive and falling back to those in the
            JS code."""
            name, paren, params = self.arguments[0].partition('(')
            return ('(%s' % params) if params else '(%s)' % ', '.join(doclet['meta']['code']['paramnames'])

        def _function_name(self):
            """Return the JS function name."""
            return self.arguments[0].split('(')[0]

    return AutoFunctionDirective
