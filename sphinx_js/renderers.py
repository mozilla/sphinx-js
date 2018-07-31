from json import dumps
from re import sub

from docutils.parsers.rst import Parser as RstParser
from docutils.statemachine import StringList
from docutils.utils import new_document
from jinja2 import Environment, PackageLoader
from six import string_types
from sphinx.errors import SphinxError
from sphinx.util import rst

from .parsers import PathVisitor
from .suffix_tree import SuffixAmbiguous, SuffixNotFound


class JsRenderer(object):
    """Abstract superclass for renderers of various sphinx-js directives

    Provides an inversion-of-control framework for rendering and bridges us
    from the hidden, closed-over JsDirective subclasses to top-level classes
    that can see and use each other. Handles parsing of a single, all-consuming
    argument that consists of a JS entity reference and an optional formal
    parameter list.

    """
    def __init__(self, directive, app, arguments=None, content=None, options=None):
        # Fix crash when calling eval_rst with CommonMarkParser:
        if not hasattr(directive.state.document.settings, 'tab_width'):
            directive.state.document.settings.tab_width = 8

        self._directive = directive

        # content, arguments, options, app: all need to be accessible to
        # template_vars, so we bring them in on construction and stow them away
        # on the instance so calls to template_vars don't need to concern
        # themselves with what it needs.
        self._app = app
        self._partial_path, self._explicit_formal_params = PathVisitor().parse(arguments[0])
        self._content = content or StringList()
        self._options = options or {}

    @classmethod
    def from_directive(cls, directive, app):
        """Return one of these whose state is all derived from a directive.

        This is suitable for top-level calls but not for when a renderer is
        being called from a different renderer, lest content and such from the
        outer directive be duplicated in the inner directive.

        :arg directive: The associated Sphinx directive
        :arg app: The Sphinx global app object. Some methods need this.

        """
        return cls(directive,
                   app,
                   arguments=directive.arguments,
                   content=directive.content,
                   options=directive.options)

    def rst_nodes(self):
        """Render into RST nodes a thing shaped like a function, having a name
        and arguments.

        Fill in args, docstrings, and info fields from stored JSDoc output.

        """
        try:
            # Get the relevant documentation together:
            doclet, full_path = self._app._sphinxjs_doclets_by_path.get_with_path(self._partial_path)
        except SuffixNotFound as exc:
            raise SphinxError('No JSDoc documentation was found for object "%s" or any path ending with that.'
                              % ''.join(exc.segments))
        except SuffixAmbiguous as exc:
            raise SphinxError('More than one JS object matches the path suffix "%s". Candidate paths have these segments in front: %s'
                              % (''.join(exc.segments), exc.next_possible_keys))
        else:
            rst = self.rst(self._partial_path,
                           full_path,
                           doclet,
                           use_short_name='short-name' in self._options)

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
        return []

    def rst(self, partial_path, full_path, doclet, use_short_name=False):
        """Return rendered RST about an entity with the given name and doclet."""
        dotted_name = partial_path[-1] if use_short_name else _dotted_path(partial_path)

        # Render to RST using Jinja:
        env = Environment(loader=PackageLoader('sphinx_js', 'templates'))
        template = env.get_template(self._template)
        return template.render(**self._template_vars(dotted_name, full_path, doclet))

    def _name(self):
        """Return the JS function or class longname."""
        return self._arguments[0].split('(')[0]

    def _formal_params(self, doclet):
        """Return the JS function or class params, looking first to any
        explicit params written into the directive and falling back to those in
        the JS code.

        Return a ReST-escaped string ready for substitution into the template.

        """
        def format_default_according_to_type_hints(value, declared_types):
            """Return the default value for a param, formatted as a string
            ready to be used in a formal parameter list.

            JSDoc is a mess at extracting default values. It can unambiguously
            extract only a few simple types from the function signature, and
            ambiguity is even more rife when extracting from doclets. So we use
            any declared types to resolve the ambiguity.

            :arg value: The extracted value, which may be of the right or wrong type
            :arg declared_types: A list of types declared in the doclet for
                this param. For example ``{string|number}`` would yield ['string',
                'number'].

            """
            def first(list, default):
                try:
                    return list[0]
                except IndexError:
                    return default

            declared_type_implies_string = first(declared_types, '') == 'string'

            # If the first item of the type disjunction is "string", we treat
            # the default value as a string. Otherwise, we don't. So, if you
            # want your ambiguously documented default like ``@param
            # {string|Array} [foo=[]]`` to be treated as a string, make sure
            # "string" comes first.
            if isinstance(value, string_types):  # JSDoc threw it to us as a string in the JSON.
                if declared_types and not declared_type_implies_string:
                    # It's a spurious string, like ``() => 5`` or a variable name.
                    # Let it through verbatim.
                    return value
                else:
                    # It's a real string.
                    return dumps(value)  # Escape any contained quotes.
            else:  # It came in as a non-string.
                if declared_type_implies_string:
                    # It came in as an int, null, or bool, and we have to
                    # convert it back to a string.
                    return '"%s"' % (dumps(value),)
                else:
                    # It's fine as the type it is.
                    return dumps(value)

        if self._explicit_formal_params:
            return self._explicit_formal_params

        # Harvest params from the @param tag unless they collide with an
        # explicit formal param. Even look at params that are really
        # documenting subproperties of formal params. Also handle param default
        # values.
        params = []
        used_names = []
        MARKER = object()

        for param in doclet.get('params', []):
            name = param['name'].split('.')[0]
            default = param.get('defaultvalue', MARKER)
            type = param.get('type', {'names': []})

            # Add '...' to the parameter name if it's a variadic argument
            if param.get('variable'):
                name = '...' + name

            if name not in used_names:
                params.append(rst.escape(name) if default is MARKER else
                              '%s=%s' % (rst.escape(name),
                                         rst.escape(format_default_according_to_type_hints(default, type['names']))))
                used_names.append(name)

        # Use params from JS code if there are no documented params:
        if not params:
            params = [rst.escape(p) for p in doclet['meta']['code'].get('paramnames', [])]

        return '(%s)' % ', '.join(params)

    def _fields(self, doclet):
        """Return an iterable of "info fields" to be included in the directive,
        like params, return values, and exceptions.

        Each field consists of a tuple ``(heads, tail)``, where heads are
        words that go between colons (as in ``:param string href:``) and
        tail comes after.

        """
        FIELD_TYPES = [('params', _params_formatter),
                       ('params', _param_type_formatter),
                       ('properties', _params_formatter),
                       ('properties', _param_type_formatter),
                       ('exceptions', _exceptions_formatter),
                       ('returns', _returns_formatter)]
        for field_name, callback in FIELD_TYPES:
            for field in doclet.get(field_name, []):
                description = field.get('description', '')
                unwrapped = sub(r'[ \t]*[\r\n]+[ \t]*', ' ', description)
                yield callback(field, unwrapped)


class AutoFunctionRenderer(JsRenderer):
    _template = 'function.rst'

    def _template_vars(self, name, full_path, doclet):
        return dict(
            name=name,
            params=self._formal_params(doclet),
            fields=self._fields(doclet),
            description=doclet.get('description', ''),
            examples=doclet.get('examples', ''),
            deprecated=doclet.get('deprecated', False),
            see_also=doclet.get('see', []),
            content='\n'.join(self._content))


class AutoClassRenderer(JsRenderer):
    _template = 'class.rst'

    def _template_vars(self, name, full_path, doclet):
        return dict(
            name=name,
            params=self._formal_params(doclet),
            fields=self._fields(doclet),
            examples=doclet.get('examples', ''),
            deprecated=doclet.get('deprecated', False),
            see_also=doclet.get('see', []),
            class_comment=doclet.get('classdesc', ''),
            constructor_comment=doclet.get('description', ''),
            content='\n'.join(self._content),
            members=self._members_of(full_path,
                                     include=self._options['members'],
                                     exclude=self._options.get('exclude-members', set()),
                                     should_include_private='private-members' in self._options)
                    if 'members' in self._options else '')

    def _members_of(self, full_path, include, exclude, should_include_private):
        """Return RST describing the members of the named class.

        :arg full_path list: The unambiguous path of the class we're documenting
        :arg include: List of names of members to include. If empty, include
            all.
        :arg exclude: Set of names of members to exclude
        :arg should_include_private: Whether to include private members

        """
        def rst_for(doclet):
            renderer = (AutoFunctionRenderer if doclet.get('kind') in ['function', 'typedef']
                        else AutoAttributeRenderer)
            # Pass a dummy arg list with no formal param list so
            # _formal_params() won't find an explicit param list in there and
            # override what it finds in the code:
            return renderer(self._directive, self._app, arguments=['dummy']).rst(
                [doclet['name']],
                'dummy_full_path',
                doclet,
                use_short_name=False)

        def doclets_to_include(include):
            """Return the doclets that should be included (before excludes and
            access specifiers are taken into account).

            This will either be the doclets explicitly listed after the
            ``:members:`` option, in that order; all doclets that are
            members of the class; or listed members with remaining ones
            inserted at the placeholder "*".

            """
            doclets = self._app._sphinxjs_doclets_by_class[tuple(full_path)]
            if not include:
                # Specifying none means listing all.
                return sorted(doclets, key=lambda d: d['name'])
            included_set = set(include)

            # If the special name * is included in the list, include
            # all other doclets, in sorted order.
            if '*' in included_set:
                star_index = include.index('*')
                not_included = sorted(d['name'] for d in doclets if d['name'] not in included_set)
                include = include[:star_index] + not_included + include[star_index + 1:]
                included_set.update(not_included)

            # Even if there are 2 doclets with the same short name (e.g. a
            # static member and an instance one), keep them both. This
            # prefiltering step should make the below sort less horrible, even
            # though I'm calling index().
            included_doclets = [d for d in doclets if d['name'] in included_set]
            # sort()'s stability should keep same-named doclets in the order
            # JSDoc spits them out in.
            included_doclets.sort(key=lambda d: include.index(d['name']))
            return included_doclets

        return '\n\n'.join(
            rst_for(doclet) for doclet in doclets_to_include(include)
            if (doclet.get('access', 'public') in ('public', 'protected')
                or (doclet.get('access') == 'private' and should_include_private))
            and doclet['name'] not in exclude)


class AutoAttributeRenderer(JsRenderer):
    _template = 'attribute.rst'

    def _template_vars(self, name, full_path, doclet):
        return dict(
            name=name,
            description=doclet.get('description', ''),
            deprecated=doclet.get('deprecated', False),
            see_also=doclet.get('see', []),
            examples=doclet.get('examples', ''),
            type='|'.join(doclet.get('type', {}).get('names', [])),
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
    heads.append(rst.escape(field['name']))
    tail = description
    return heads, tail


def _param_type_formatter(field, description):
    """Generate types for function parameters specified in field."""
    heads = ['type', field['name']]
    tail = _or_types(field)
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
    with vertical bars between them, like "number|string".

    ReST-escape the types.

    """
    return rst.escape('|'.join(field.get('type', {}).get('names', [])))


def _dotted_path(segments):
    """Convert a JS object path (``['dir/', 'file/', 'class#',
    'instanceMethod']``) to a dotted style that Sphinx will better index."""
    segments_without_separators = [s[:-1] for s in segments[:-1]]
    segments_without_separators.append(segments[-1])
    return '.'.join(segments_without_separators)
