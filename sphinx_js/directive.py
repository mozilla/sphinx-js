from docutils import nodes
from docutils.parsers.rst import Directive, directives
from docutils.statemachine import ViewList
from sphinx.util.docstrings import prepare_docstring


class AutoConfigDirective(Directive):
    has_content = True
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = False

    option_spec = {
        # Whether or not to show the class docstring--if None, don't show the
        # docstring, if empty string use __doc__, otherwise use the value of
        # the attribute on the class
        'show-docstring': directives.unchanged,

        # Whether or not to hide the class name
        'hide-classname': directives.flag,

        # Prepend a specified namespace
        'namespace': directives.unchanged
    }

    def run(self):
        self.reporter = self.state.document.reporter
        result = ViewList()
        result.append('Hello, Dolly!', 'someplace')

        node = nodes.paragraph()
        node.document = self.state.document
        self.state.nested_parse(result, 0, node)
        return node.children
