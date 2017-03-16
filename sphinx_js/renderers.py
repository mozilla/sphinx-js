from collections import OrderedDict
from os.path import dirname, join
from re import sub

from docutils.parsers.rst import Parser as RstParser
from docutils.utils import new_document
from jinja2 import Environment, PackageLoader
from six import iteritems
from sphinx.ext.autodoc import ALL


class JsRenderer(object):
    """Abstract superclass for renderers of various sphinx-js directives

    Provides an inversion-of-control framework for rendering and bridges us
    from the hidden, closed-over JsDirective subclasses to top-level classes
    that can see and use each other.

    """
    def __init__(self, directive, app):
        """
        :arg directive: The associated Sphinx directive
        :arg app: The Sphinx global app object. Some methods need this.
        """
        # content, arguments, options, app: all need to be accessible to
        # template_vars, so we bring them in as constructor params and stow
        # them away on the instance so calls to template_vars don't need to
        # concern themselves with what it needs.
        self._arguments = directive.arguments
        self._content = directive.content
        self._options = directive.options
        self._directive = directive
        self._app = app
    
    def rst_nodes(self):
        """Render into RST nodes a thing shaped like a function, having a name
        and arguments.

        Fill in args, docstrings, and info fields from stored JSDoc output.

        """
        # Get the relevant documentation together:
        name = self._name()
        doclet = self._app._sphinxjs_doclets_by_longname.get(name)
        if doclet is None:
            app.warn('No JSDoc documentation for the longname "%s" was found.' % name)
            return []
        rst = self.rst(name, doclet, use_short_name='short-name' in self._options)

        # Parse the RST into docutils nodes with a fresh doc, and return
        # them.
        #
        # Not sure if passing the settings from the "real" doc is the right
        # thing to do here:
        meta = doclet['meta']
        doc = new_document('%s:%s(%s)' % (meta['filename'],
                                          doclet['longname'],
                                          meta['lineno']),
                           settings=self._directive.state.document.settings)
        RstParser().parse(rst, doc)
        return doc.children

    def rst(self, name, doclet, use_short_name=False):
        """Return rendered RST about an entity with the given name and doclet."""
        dotted_name = _namepath_to_dotted(name)
        if use_short_name:
            dotted_name = dotted_name.split('.')[-1]

        # Render to RST using Jinja:
        env = Environment(loader=PackageLoader('sphinx_js', 'templates'))
        template = env.get_template(self._template)
        return template.render(**self._template_vars(dotted_name, doclet))

    def _name(self):
        """Return the JS function or class longname."""
        return self._arguments[0].split('(')[0]

    def _formal_params(self, doclet):
        """Return the JS function or class params, looking first to any
        explicit params written into the directive and falling back to
        those in the JS code."""
        name, paren, params = self._arguments[0].partition('(')
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


class AutoFunctionRenderer(JsRenderer):
    _template = 'function.rst'

    def _template_vars(self, name, doclet):
        return dict(
            name=name,
            params=self._formal_params(doclet),
            fields=self._fields(doclet),
            description=doclet.get('description', ''),
            content='\n'.join(self._content))


class AutoClassRenderer(JsRenderer):
    _template = 'class.rst'

    def _template_vars(self, name, doclet):
        return dict(
            name=name,
            params=self._formal_params(doclet),
            fields=self._fields(doclet),
            class_comment=doclet.get('classdesc', ''),
            constructor_comment=doclet.get('description', ''),
            content='\n'.join(self._content),
            members=self._members_of(
                name,
                exclude=self._options.get('exclude-members', set()),
                include_private=self._options.get('private-members', False))
                if 'members' in self._options else '')

    def _members_of(self, name, exclude, include_private):
        """Return RST describing the members of the named class.

        :arg exclude: Set of names of members to exclude
        :arg include_private: Whether to include private members

        """
        def rst_for(doclet):
            renderer = (AutoFunctionRenderer if doclet.get('kind') == 'function'
                        else AutoAttributeRenderer)
            return renderer(self._directive, self._app).rst(
                doclet['longname'],
                doclet,
                use_short_name=False)
        return '\n\n'.join(rst_for(doclet) for doclet in
                           self._app._sphinxjs_doclets_by_class[name])


class AutoAttributeRenderer(JsRenderer):
    _template = 'attribute.rst'

    def _template_vars(self, name, doclet):
        return dict(
            name=name,
            description=doclet.get('description', ''),
            content='\n'.join(self._content))


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
