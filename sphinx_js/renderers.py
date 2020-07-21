from docutils.parsers.rst import Parser as RstParser
from docutils.statemachine import StringList
from docutils.utils import new_document
from jinja2 import Environment, PackageLoader
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
            doclet = self._app._sphinxjs_analyzer.get_object(
                self._partial_path, self._renderer_type)
        except SuffixNotFound as exc:
            raise SphinxError('No JSDoc documentation was found for object "%s" or any path ending with that.'
                              % ''.join(exc.segments))
        except SuffixAmbiguous as exc:
            raise SphinxError('More than one object matches the path suffix "%s". Candidate paths have these segments in front: %s'
                              % (''.join(exc.segments), exc.next_possible_keys))
        else:
            rst = self.rst(self._partial_path,
                           doclet,
                           use_short_name='short-name' in self._options)

            # Parse the RST into docutils nodes with a fresh doc, and return
            # them.
            #
            # Not sure if passing the settings from the "real" doc is the right
            # thing to do here:
            doc = new_document('%s:%s(%s)' % (doclet.filename,
                                              doclet.path,
                                              doclet.line),
                               settings=self._directive.state.document.settings)
            RstParser().parse(rst, doc)
            return doc.children
        return []

    def rst(self, partial_path, doclet, use_short_name=False):
        """Return rendered RST about an entity with the given name and doclet."""
        dotted_name = partial_path[-1] if use_short_name else _dotted_path(partial_path)

        # Render to RST using Jinja:
        env = Environment(loader=PackageLoader('sphinx_js', 'templates'))
        template = env.get_template(self._template)
        return template.render(**self._template_vars(dotted_name, doclet))

    def _name(self):
        """Return the JS function or class longname."""
        return self._arguments[0].split('(')[0]

    def _formal_params(self, doclet):
        """Return the JS function or class params, looking first to any
        explicit params written into the directive and falling back to those in
        the JS code.

        Return a ReST-escaped string ready for substitution into the template.

        """
        if self._explicit_formal_params:
            return self._explicit_formal_params

        # Harvest params from the @param tag unless they collide with an
        # explicit formal param. Even look at params that are really
        # documenting subproperties of formal params. Also handle param default
        # values.
        formals = []
        used_names = set()

        for param in doclet.params:
            name = param.name
            default = param.default

            # Add '...' to the parameter name if it's a variadic argument
            if param.is_variadic:
                name = '...' + name

            if name not in used_names:
                # We don't rst.escape() anything here, because, empirically,
                # the js:function directive (or maybe directive params in
                # general) automatically ignores markup constructs in its
                # parameter (though not its contents).
                formals.append(name if not param.has_default else
                               '%s=%s' % (name, param.default))
                used_names.add(name)

        return '(%s)' % ', '.join(formals)

    def _fields(self, doclet):
        """Return an iterable of "info fields" to be included in the directive,
        like params, return values, and exceptions.

        Each field consists of a tuple ``(heads, tail)``, where heads are
        words that go between colons (as in ``:param string href:``) and
        tail comes after.

        """
        FIELD_TYPES = [('params', _param_formatter),
                       ('params', _param_type_formatter),
                       ('properties', _param_formatter),
                       ('properties', _param_type_formatter),
                       ('exceptions', _exception_formatter),
                       ('returns', _return_formatter)]
        for collection_attr, callback in FIELD_TYPES:
            for instance in getattr(doclet, collection_attr, []):
                heads, tail = callback(instance, instance.description)
                yield [rst.escape(h) for h in heads], tail


class AutoFunctionRenderer(JsRenderer):
    _template = 'function.rst'
    _renderer_type = 'function'

    def _template_vars(self, name, doclet):
        return dict(
            name=name,
            params=self._formal_params(doclet),
            fields=self._fields(doclet),
            description=doclet.description,
            examples=doclet.examples,
            deprecated=doclet.deprecated,
            see_also=doclet.see_alsos,
            content='\n'.join(self._content))


class AutoClassRenderer(JsRenderer):
    _template = 'class.rst'
    _renderer_type = 'class'

    def _template_vars(self, name, doclet):
        return dict(
            name=name,
            params=self._formal_params(doclet),
            fields=self._fields(doclet),
            examples=doclet.examples,
            deprecated=doclet.deprecated,
            see_also=doclet.see_alsos,
            class_comment=doclet.description,
            constructor_comment=doclet.constructor_description,
            content='\n'.join(self._content),
            # NEXT: See if we can get some unit tests going. ir.py still needs to be written.
            members=self._members_of(doclet,
                                     include=self._options['members'],
                                     exclude=self._options.get('exclude-members', set()),
                                     should_include_private='private-members' in self._options)
                    if 'members' in self._options else '')

    def _members_of(self, doclet, include, exclude, should_include_private):
        """Return RST describing the members of a given class.

        :arg doclet Class: The class we're documenting
        :arg include: List of names of members to include. If empty, include
            all.
        :arg exclude: Set of names of members to exclude
        :arg should_include_private: Whether to include private members

        """
        def rst_for(doclet):
            renderer = (AutoFunctionRenderer if isinstance(doclet, Function)
                        else AutoAttributeRenderer)
            # Pass a dummy arg list with no formal param list so
            # _formal_params() won't find an explicit param list in there and
            # override what it finds in the code:
            return renderer(self._directive, self._app, arguments=['dummy']).rst(
                [doclet.name],
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
            doclets = doclet.members
            if not include:
                # Specifying none means listing all.
                return sorted(doclets, key=lambda d: d.path_segments)  # TODO: If path_segments is empty, fall back to d.name like this used to pre-IR.
            included_set = set(include)

            # If the special name * is included in the list, include
            # all other doclets, in sorted order.
            if '*' in included_set:
                star_index = include.index('*')
                sorted_not_included_doclets = sorted(
                    (d for d in doclets if d.name not in included_set),
                    key=lambda d: d.path_segments  # TODO: Fall back to d.name if needed like it used to.
                )
                not_included = [d.name for d in sorted_not_included_doclets]
                include = include[:star_index] + not_included + include[star_index + 1:]
                included_set.update(not_included)

            # Even if there are 2 doclets with the same short name (e.g. a
            # static member and an instance one), keep them both. This
            # prefiltering step should make the below sort less horrible, even
            # though I'm calling index().
            included_doclets = [d for d in doclets if d.name in included_set]
            # sort()'s stability should keep same-named doclets in the order
            # JSDoc spits them out in.
            included_doclets.sort(key=lambda d: include.index(d.name))
            return included_doclets
            # TODO: Quit saying "doclets" where what we really mean is IR entities.

        return '\n\n'.join(
            rst_for(doclet) for doclet in doclets_to_include(include)
            if (not doclet.is_private()
                or (doclet.is_private and should_include_private))
            and doclet.name not in exclude)


class AutoAttributeRenderer(JsRenderer):
    _template = 'attribute.rst'
    _renderer_type = 'attribute'

    def _template_vars(self, name, doclet):
        return dict(
            name=name,
            description=doclet.description,
            deprecated=doclet.deprecated,
            see_also=doclet.see_alsos,
            examples=doclet.examples,
            type=_or_types(doclet.types),
            content='\n'.join(self._content))


def _return_formatter(return_):
    """Derive heads and tail from ``@returns`` blocks."""
    types = _or_types(return_)
    tail = ('**%s** -- ' % rst.escape(types)) if types else ''
    tail += return_.description
    return ['returns'], tail


def _param_formatter(param):
    """Derive heads and tail from ``@param`` blocks."""
    heads = ['param']
    types = _or_types(param.types)
    if types:
        heads.append(types)
    heads.append(param.name)
    tail = param.description
    return heads, tail


def _param_type_formatter(param):
    """Generate types for function parameters specified in field."""
    # TODO: I'm not sure what this does.
    heads = ['type', param.name]
    tail = rst.escape(_or_types(param.types))
    return heads, tail


def _exception_formatter(exception):
    """Derive heads and tail from ``@throws`` blocks."""
    heads = ['throws']
    types = _or_types(exception.types)
    if types:
        heads.append(types)
    tail = exception.description
    return heads, tail


def _or_types(types):
    """Return all the types in a doclet subfield like "params" or "returns"
    with vertical bars between them, like "number|string".

    """
    return '|'.join(types)


def _dotted_path(segments):
    """Convert a JS object path (``['dir/', 'file/', 'class#',
    'instanceMethod']``) to a dotted style that Sphinx will better index."""
    segments_without_separators = [s[:-1] for s in segments[:-1]]
    segments_without_separators.append(segments[-1])
    return '.'.join(segments_without_separators)
