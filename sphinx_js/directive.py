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
        has_content = True
        required_arguments = 1
        optional_arguments = 0

        option_spec = {}

        def run(self):
            # Get the relevant documentation out of storage:
            doclet = app._sphinxjs_jsdoc_output[self.arguments[0]]

            # Render to RST using Jinja:
            env = Environment(loader=FileSystemLoader(join(dirname(__file__), 'templates')))
            template = env.get_template('function.rst')
            rst = template.render(
                name=doclet.get('name', ''),
                args=', '.join(doclet['meta']['code']['paramnames']),
                description=doclet.get('description', ''))
            # TODO: Deal with the case where people manually type params after
            # the function name.

            # Parse the RST into docutils nodes with a fresh doc, and return
            # them:
            #
            # Not sure if passing the settings from the "real" doc is the right
            # thing to do here:
            doc = new_document('dummy', settings=self.state.document.settings)
            RstParser().parse(rst, doc)
            return doc.children

    return AutoFunctionDirective
