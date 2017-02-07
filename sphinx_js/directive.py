from os.path import dirname, join
from re import sub

from docutils.parsers.rst import Directive, Parser as RstParser
from docutils.utils import new_document
from jinja2 import Environment, PackageLoader
from six import iteritems


def auto_function_directive_bound_to_app(app):
    """Give the js:autofunction directive access to the Sphinx app singleton by
    closing over it.

    That's where we store the JSDoc output.

    """
    class AutoFunctionDirective(Directive):
        """js:autofunction directive, which spits out a js:function directive

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
            name = self._name()
            doclet = app._sphinxjs_jsdoc_output.get(name)
            if doclet is None:
                app.warn('No JSDoc documentation for the longname "%s" was found.' % name)
                return []

            # Render to RST using Jinja:
            env = Environment(loader=PackageLoader('sphinx_js', 'templates'))
            template = env.get_template('function.rst')
            rst = template.render(
                name=_namepath_to_dotted(name),
                params=self._formal_params(doclet),
                fields=self._fields(doclet),
                description=doclet.get('description', ''),
                content='\n'.join(self.content))

            # Parse the RST into docutils nodes with a fresh doc, and return
            # them:
            #
            # Not sure if passing the settings from the "real" doc is the right
            # thing to do here:
            doc = new_document('dummy', settings=self.state.document.settings)
            RstParser().parse(rst, doc)
            return doc.children

        def _formal_params(self, doclet):
            """Return the JS function params, looking first to any explicit
            params written into the directive and falling back to those in the
            JS code."""
            name, paren, params = self.arguments[0].partition('(')
            return ('(%s' % params) if params else '(%s)' % ', '.join(doclet['meta']['code']['paramnames'])

        def _name(self):
            """Return the JS function name."""
            return self.arguments[0].split('(')[0]

        def _fields(self, doclet):
            """Return an iterable of "fields" to be included in the js:function directive, like params, return values, and exceptions.

            Each field consists of a tuple ``(heads, tail)``, where heads are
            words that go between colons (as in ``:param string href:``) and
            tail comes after.

            """
            FIELD_TYPES = {'returns': _returns_formatter,
                           'params': _params_formatter,
                           'exceptions': _exceptions_formatter}
            for field_name, callback in iteritems(FIELD_TYPES):
                for field in doclet.get(field_name, []):
                    yield callback(field)

    return AutoFunctionDirective


def _returns_formatter(field):
    """Derive heads and tail from ``@returns`` blocks."""
    types = _or_types(field)
    tail = ('**%s** -- ' % types) if types else ''
    tail += field.get('description', '')
    return ['returns'], tail


def _params_formatter(field):
    """Derive heads and tail from ``@param`` blocks."""
    heads = ['param']
    types = _or_types(field)
    if types:
        heads.append(types)
    heads.append(field['name'])
    tail = field.get('description', '')
    return heads, tail


def _exceptions_formatter(field):
    """Derive heads and tail from ``@throws`` blocks."""
    heads = ['throws']
    types = _or_types(field)
    if types:
        heads.append(types)
    tail = field.get('description', '')
    return heads, tail


def _or_types(field):
    """Return all the types in a doclet subfield like "params" or "returns"
    with vertical bars between them, like "number|string"."""
    return '|'.join(field.get('type', {}).get('names', []))


def _namepath_to_dotted(namepath):
    """Convert a node.js-style namepath (``class#instanceMethod``) to a dotted
    style that Sphinx will better index."""
    # TODO: Handle "module:"
    # TODO: Skip backslash-escaped .~#, which are proper parts of names.
    return sub('[#~-]', '.', namepath)  # - is for JSDoc 2.
