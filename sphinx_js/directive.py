from collections import OrderedDict
from os.path import dirname, join
from re import sub

from docutils.parsers.rst import Directive, Parser as RstParser
from docutils.parsers.rst.directives import flag
from docutils.utils import new_document
from jinja2 import Environment, PackageLoader
from six import iteritems


class JsDirective(Directive):
    """Abstract directive which knows how to pull things out of JSDoc output"""

    has_content = True
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = True

    option_spec = {
        'short-name': flag
    }

    def _run(self, app):
        """Render a thing shaped like a function, having a name and arguments.

        Fill in args, docstrings, and info fields from stored JSDoc output.

        """
        # Get the relevant documentation together:
        name = self._name()
        dotted_name = _namepath_to_dotted(name)
        if 'short-name' in self.options:
            dotted_name = dotted_name.split('.')[-1]
        doclet = app._sphinxjs_jsdoc_output.get(name)
        if doclet is None:
            app.warn('No JSDoc documentation for the longname "%s" was found.' % name)
            return []

        # Render to RST using Jinja:
        env = Environment(loader=PackageLoader('sphinx_js', 'templates'))
        template = env.get_template(self._template)
        rst = template.render(**self._template_vars(dotted_name, doclet))

        # Parse the RST into docutils nodes with a fresh doc, and return
        # them.
        #
        # Not sure if passing the settings from the "real" doc is the right
        # thing to do here:
        meta = doclet['meta']
        doc = new_document('%s:%s(%s)' % (meta['filename'],
                                          doclet['longname'],
                                          meta['lineno']),
                           settings=self.state.document.settings)
        RstParser().parse(rst, doc)
        return doc.children

    def _name(self):
        """Return the JS function or class name."""
        return self.arguments[0].split('(')[0]

    def _formal_params(self, doclet):
        """Return the JS function or class params, looking first to any
        explicit params written into the directive and falling back to
        those in the JS code."""
        name, paren, params = self.arguments[0].partition('(')
        return ('(%s' % params) if params else '(%s)' % ', '.join(doclet['meta']['code']['paramnames'])

    def _fields(self, doclet):
        """Return an iterable of "info fields" to be included in the directive,
        like params, return values, and exceptions.

        Each field consists of a tuple ``(heads, tail)``, where heads are
        words that go between colons (as in ``:param string href:``) and
        tail comes after.

        """
        FIELD_TYPES = OrderedDict([('params', _params_formatter),
                                   ('exceptions', _exceptions_formatter),
                                   ('returns', _returns_formatter)])
        for field_name, callback in iteritems(FIELD_TYPES):
            for field in doclet.get(field_name, []):
                description = field.get('description', '')
                unwrapped = sub(r'[ \t]*\n[ \t]*', ' ', description)
                yield callback(field, unwrapped)


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
        _template = 'function.rst'

        def run(self):
            return self._run(app)

        def _template_vars(self, name, doclet):
            return dict(
                name=name,
                params=self._formal_params(doclet),
                fields=self._fields(doclet),
                description=doclet.get('description', ''),
                content='\n'.join(self.content))

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
        _template = 'class.rst'

        def run(self):
            return self._run(app)

        def _template_vars(self, name, doclet):
            return dict(
                name=name,
                params=self._formal_params(doclet),
                fields=self._fields(doclet),
                class_comment=doclet.get('classdesc', ''),
                constructor_comment=doclet.get('description', ''),
                content='\n'.join(self.content))

    return AutoClassDirective


def auto_attribute_directive_bound_to_app(app):
    """Give the js:autoattribute directive access to the Sphinx app singleton
    by closing over it."""

    class AutoAttributeDirective(JsDirective):
        """js:autoattribute directive, which spits out a js:attribute directive

        Takes a single argument which is a JS attribute name.

        """
        _template = 'attribute.rst'

        def run(self):
            return self._run(app)

        def _template_vars(self, name, doclet):
            return dict(
                name=name,
                description=doclet.get('description', ''),
                content='\n'.join(self.content))

    return AutoAttributeDirective


def _returns_formatter(field, description):
    """Derive heads and tail from ``@returns`` blocks."""
    types = _or_types(field)
    tail = ('**%s** -- ' % types) if types else ''
    tail += description
    return ['returns'], tail


def _params_formatter(field, description):
    """Derive heads and tail from ``@param`` blocks."""
    heads = ['param']
    types = _or_types(field)
    if types:
        heads.append(types)
    heads.append(field['name'])
    tail = description
    return heads, tail


def _exceptions_formatter(field, description):
    """Derive heads and tail from ``@throws`` blocks."""
    heads = ['throws']
    types = _or_types(field)
    if types:
        heads.append(types)
    tail = description
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
    return sub(r'[#~-]', '.', namepath)  # - is for JSDoc 2.
