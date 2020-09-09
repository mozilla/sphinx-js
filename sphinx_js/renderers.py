from re import sub

from docutils.parsers.rst import Parser as RstParser
from docutils.statemachine import StringList
from docutils.utils import new_document
from jinja2 import Environment, PackageLoader
from sphinx.errors import SphinxError
from sphinx.util import rst

from .analyzer_utils import dotted_path
from .ir import Class, Function, Interface, Pathname
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
            obj = self._app._sphinxjs_analyzer.get_object(
                self._partial_path, self._renderer_type)
        except SuffixNotFound as exc:
            raise SphinxError('No JSDoc documentation was found for object "%s" or any path ending with that.'
                              % ''.join(exc.segments))
        except SuffixAmbiguous as exc:
            raise SphinxError('More than one object matches the path suffix "%s". Candidate paths have these segments in front: %s'
                              % (''.join(exc.segments), exc.next_possible_keys))
        else:
            rst = self.rst(self._partial_path,
                           obj,
                           use_short_name='short-name' in self._options)

            # Parse the RST into docutils nodes with a fresh doc, and return
            # them.
            #
            # Not sure if passing the settings from the "real" doc is the right
            # thing to do here:
            doc = new_document('%s:%s(%s)' % (obj.filename,
                                              obj.path,
                                              obj.line),
                               settings=self._directive.state.document.settings)
            RstParser().parse(rst, doc)
            return doc.children
        return []

    def rst(self, partial_path, obj, use_short_name=False):
        """Return rendered RST about an entity with the given name and IR
        object."""
        dotted_name = partial_path[-1] if use_short_name else dotted_path(partial_path)

        # Render to RST using Jinja:
        env = Environment(loader=PackageLoader('sphinx_js', 'templates'))
        template = env.get_template(self._template)
        return template.render(**self._template_vars(dotted_name, obj))

    def _formal_params(self, obj):
        """Return the JS function or class params, looking first to any
        explicit params written into the directive and falling back to those in
        comments or JS code.

        Return a ReST-escaped string ready for substitution into the template.

        """
        if self._explicit_formal_params:
            return self._explicit_formal_params

        formals = []
        used_names = set()

        for param in obj.params:
            # Turn "@param p2.subProperty" into just p2. We wouldn't want to
            # add subproperties to the flat formal param list:
            name = param.name.split('.')[0]

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

    def _fields(self, obj):
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
            for instance in getattr(obj, collection_attr, []):
                result = callback(instance)
                if result:
                    heads, tail = result
                    # If there are line breaks in the tail, the RST parser will
                    # end the field list prematurely.
                    #
                    # TODO: Instead, indent multi-line tails juuuust right, and
                    # we can enjoy block-level constructs within tails:
                    # https://docutils.sourceforge.io/docs/ref/rst/
                    # restructuredtext.html#field-lists.
                    yield [rst.escape(h) for h in heads], unwrapped(tail)


class AutoFunctionRenderer(JsRenderer):
    _template = 'function.rst'
    _renderer_type = 'function'

    def _template_vars(self, name, obj):
        return dict(
            name=name,
            params=self._formal_params(obj),
            fields=self._fields(obj),
            description=obj.description,
            examples=obj.examples,
            deprecated=obj.deprecated,
            is_optional=obj.is_optional,
            see_also=obj.see_alsos,
            content='\n'.join(self._content))


class AutoClassRenderer(JsRenderer):
    _template = 'class.rst'
    _renderer_type = 'class'

    def _template_vars(self, name, obj):
        # TODO: At the moment, we pull most fields (params, returns,
        # exceptions, etc.) off the constructor only. We could pull them off
        # the class itself too in the future.
        if not isinstance(obj, Class) or not obj.constructor:
            # One way or another, it has no constructor, so make a blank one to
            # keep from repeating this long test for every constructor-using
            # line in the dict() call:
            constructor = Function(
                name='',
                path=Pathname([]),
                filename='',
                description='',
                line=0,
                deprecated=False,
                examples=[],
                see_alsos=[],
                properties=[],
                exported_from=None,
                is_abstract=False,
                is_optional=False,
                is_static=False,
                is_private=False,
                params=[],
                exceptions=[],
                returns=[])
        else:
            constructor = obj.constructor
        return dict(
            name=name,
            params=self._formal_params(constructor),
            fields=self._fields(constructor),
            examples=constructor.examples,
            deprecated=constructor.deprecated,
            see_also=constructor.see_alsos,
            exported_from=obj.exported_from,
            class_comment=obj.description,
            is_abstract=isinstance(obj, Class) and obj.is_abstract,
            interfaces=obj.interfaces if isinstance(obj, Class) else [],
            is_interface=isinstance(obj, Interface),  # TODO: Make interfaces not look so much like classes. This will require taking complete control of templating from Sphinx.
            supers=obj.supers,
            constructor_comment=constructor.description,
            content='\n'.join(self._content),
            members=self._members_of(obj,
                                     include=self._options['members'],
                                     exclude=self._options.get('exclude-members', set()),
                                     should_include_private='private-members' in self._options)
                    if 'members' in self._options else '')

    def _members_of(self, obj, include, exclude, should_include_private):
        """Return RST describing the members of a given class.

        :arg obj Class: The class we're documenting
        :arg include: List of names of members to include. If empty, include
            all.
        :arg exclude: Set of names of members to exclude
        :arg should_include_private: Whether to include private members

        """
        def rst_for(obj):
            renderer = (AutoFunctionRenderer if isinstance(obj, Function)
                        else AutoAttributeRenderer)
            return renderer(self._directive, self._app, arguments=['dummy']).rst(
                [obj.name],
                obj,
                use_short_name=False)

        def members_to_include(include):
            """Return the members that should be included (before excludes and
            access specifiers are taken into account).

            This will either be the ones explicitly listed after the
            ``:members:`` option, in that order; all members of the class; or
            listed members with remaining ones inserted at the placeholder "*".

            """
            def sort_attributes_first_then_by_path(obj):
                """Return a sort key for IR objects."""
                return isinstance(obj, Function), obj.path.segments

            members = obj.members
            if not include:
                # Specifying none means listing all.
                return sorted(members, key=sort_attributes_first_then_by_path)
            included_set = set(include)

            # If the special name * is included in the list, include all other
            # members, in sorted order.
            if '*' in included_set:
                star_index = include.index('*')
                sorted_not_included_members = sorted(
                    (m for m in members if m.name not in included_set),
                    key=sort_attributes_first_then_by_path
                )
                not_included = [m.name for m in sorted_not_included_members]
                include = include[:star_index] + not_included + include[star_index + 1:]
                included_set.update(not_included)

            # Even if there are 2 members with the same short name (e.g. a
            # static member and an instance one), keep them both. This
            # prefiltering step should make the below sort less horrible, even
            # though I'm calling index().
            included_members = [m for m in members if m.name in included_set]
            # sort()'s stability should keep same-named members in the order
            # JSDoc spits them out in.
            included_members.sort(key=lambda m: include.index(m.name))
            return included_members

        return '\n\n'.join(
            rst_for(member) for member in members_to_include(include)
            if (not member.is_private
                or (member.is_private and should_include_private))
            and member.name not in exclude)


class AutoAttributeRenderer(JsRenderer):
    _template = 'attribute.rst'
    _renderer_type = 'attribute'

    def _template_vars(self, name, obj):
        return dict(
            name=name,
            description=obj.description,
            deprecated=obj.deprecated,
            is_optional=obj.is_optional,
            see_also=obj.see_alsos,
            examples=obj.examples,
            type=obj.type,
            content='\n'.join(self._content))


def unwrapped(text):
    """Return the text with line wrapping removed."""
    return sub(r'[ \t]*[\r\n]+[ \t]*', ' ', text)


def _return_formatter(return_):
    """Derive heads and tail from ``@returns`` blocks."""
    tail = ('**%s** -- ' % rst.escape(return_.type)) if return_.type else ''
    tail += return_.description
    return ['returns'], tail


def _param_formatter(param):
    """Derive heads and tail from ``@param`` blocks."""
    if not param.type and not param.description:
        # There's nothing worth saying about this param.
        return None
    heads = ['param']
    if param.type:
        heads.append(param.type)
    heads.append(param.name)
    tail = param.description
    return heads, tail


def _param_type_formatter(param):
    """Generate types for function parameters specified in field."""
    if not param.type:
        return None
    heads = ['type', param.name]
    tail = rst.escape(param.type)
    return heads, tail


def _exception_formatter(exception):
    """Derive heads and tail from ``@throws`` blocks."""
    heads = ['throws']
    if exception.type:
        heads.append(exception.type)
    tail = exception.description
    return heads, tail
