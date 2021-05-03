"""JavaScript analyzer

Analyzers run jsdoc or typedoc or whatever, squirrel away their output, and
then lazily constitute IR objects as requested.

"""
from codecs import getreader, getwriter
from collections import defaultdict
from errno import ENOENT
from json import load, dumps
from os.path import join, normpath, relpath, splitext, sep
import subprocess
from tempfile import TemporaryFile

from sphinx.errors import SphinxError

from .analyzer_utils import cache_to_file, Command, is_explicitly_rooted
from .ir import Attribute, Class, Exc, Function, Namespace, NO_DEFAULT, Param, Pathname, Return
from .parsers import path_and_formal_params, PathVisitor
from .suffix_tree import SuffixTree


class Analyzer:
    """A runner of a langauge-specific static analysis tool and translator of
    the results to our IR

    """
    def __init__(self, json, base_dir):
        """Index and squirrel away the JSON for later lazy conversion to IR
        objects.

        :arg json: The loaded JSON output from jsdoc
        :arg base_dir: Resolve paths in the JSON relative to this directory.
            This must be an absolute pathname.

        """
        self._base_dir = base_dir
        # 2 doclets are made for classes, and they are largely redundant: one
        # for the class itself and another for the constructor. However, the
        # constructor one gets merged into the class one and is intentionally
        # marked as undocumented, even if it isn't. See
        # https://github.com/jsdoc3/jsdoc/issues/1129.
        doclets = [doclet for doclet in json if doclet.get('comment') and
                                                not doclet.get('undocumented')]

        # Build table for lookup by name, which most directives use:
        self._doclets_by_path = SuffixTree()
        self._doclets_by_path.add_many((full_path_segments(d, base_dir), d)
                                       for d in doclets)

        # Build lookup table for autoclass's :members: option. This will also
        # pick up members of functions (inner variables), but it will instantly
        # filter almost all of them back out again because they're
        # undocumented. We index these by unambiguous full path. Then, when
        # looking them up by arbitrary name segment, we disambiguate that first
        # by running it through the suffix tree above. Expect trouble due to
        # jsdoc's habit of calling things (like ES6 class methods)
        # "<anonymous>" in the memberof field, even though they have names.
        # This will lead to multiple methods having each other's members. But
        # if you don't have same-named inner functions or inner variables that
        # are documented, you shouldn't have trouble.
        self._doclets_by_class = defaultdict(lambda: [])
        self._doclets_by_namespace = defaultdict(lambda: [])
        for d in doclets:
            of = d.get('memberof')
            if of:  # speed optimization
                segments = full_path_segments(d, base_dir, longname_field='memberof')
                # append members to class and namespace
                self._doclets_by_class[tuple(segments)].append(d)
                self._doclets_by_namespace[tuple(segments)].append(d)

    @classmethod
    def from_disk(cls, abs_source_paths, app, base_dir):
        json = jsdoc_output(getattr(app.config, 'jsdoc_cache', None),
                            abs_source_paths,
                            base_dir,
                            app.confdir,
                            getattr(app.config, 'jsdoc_config_path', None))
        return cls(json, base_dir)

    def get_object(self, path_suffix, as_type):
        """Return the IR object with the given path suffix.

        If helpful, use the ``as_type`` hint, which identifies which autodoc
        directive the user called.

        """
        # Design note: Originally, I had planned to eagerly convert all the
        # doclets to the IR. But it's hard to tell unambiguously what kind
        # each doclet is, at least in the case of jsdoc. If instead we lazily
        # convert each doclet as it's referenced by an autodoc directive, we
        # can use the hint we previously did: the user saying "this is a
        # function (by using autofunction on it)", "this is a class", etc.
        # Additionally, being lazy lets us avoid converting unused doclets
        # altogether.
        try:
            doclet_as_whatever = {
                'function': self._doclet_as_function,
                'class': self._doclet_as_class,
                'namespace': self._doclet_as_namespace,
                'attribute': self._doclet_as_attribute}[as_type]
        except KeyError:
            raise NotImplementedError('Unknown autodoc directive: auto%s' % as_type)

        doclet, full_path = self._doclets_by_path.get_with_path(path_suffix)
        return doclet_as_whatever(doclet, full_path)

    def _doclet_as_class(self, doclet, full_path):
        # This is an instance method so it can get at the base dir.
        members = []
        for member_doclet in self._doclets_by_class[tuple(full_path)]:
            kind = member_doclet.get('kind')
            member_full_path = full_path_segments(member_doclet, self._base_dir)
            # Typedefs should still fit into function-shaped holes:
            doclet_as_whatever = self._doclet_as_function if (kind == 'function' or kind == 'typedef') else self._doclet_as_attribute
            member = doclet_as_whatever(member_doclet, member_full_path)
            members.append(member)
        return Class(
            description=doclet.get('classdesc', ''),
            supers=[],  # Could implement for JS later.
            exported_from=None,  # Could implement for JS later.
            is_abstract=False,
            interfaces=[],
            # Right now, a class generates several doclets, all but one of
            # which are marked as undocumented. In the one that's left, most of
            # the fields are about the default constructor:
            constructor=self._doclet_as_function(doclet, full_path),
            members=members,
            **top_level_properties(doclet, full_path))

    def _doclet_as_namespace(self, doclet, full_path):
        # This is an instance method so it can get at the base dir.
        members = []
        for member_doclet in self._doclets_by_namespace[tuple(full_path)]:
            kind = member_doclet.get('kind')
            member_full_path = full_path_segments(member_doclet, self._base_dir)
            # Typedefs should still fit into function-shaped holes:
            doclet_as_whatever = self._doclet_as_function if (kind == 'function' or kind == 'typedef') else self._doclet_as_attribute
            member = doclet_as_whatever(member_doclet, member_full_path)
            members.append(member)
        return Namespace(
            description=doclet.get('description', ''),
            members=members,
            exported_from=None,
            **top_level_properties(doclet, full_path))

    @staticmethod
    def _doclet_as_function(doclet, full_path):
        return Function(
            description=description(doclet),
            exported_from=None,
            is_abstract=False,
            is_optional=False,
            is_static=False,
            is_private=is_private(doclet),
            exceptions=exceptions_to_ir(doclet.get('exceptions', [])),
            returns=returns_to_ir(doclet.get('returns', [])),
            params=params_to_ir(doclet),
            **top_level_properties(doclet, full_path))

    @staticmethod
    def _doclet_as_attribute(doclet, full_path):
        return Attribute(
            description=description(doclet),
            exported_from=None,
            is_abstract=False,
            is_optional=False,
            is_static=False,
            is_private=is_private(doclet),
            type=get_type(doclet),
            **top_level_properties(doclet, full_path)
        )


def is_private(doclet):
    return doclet.get('access') == 'private'


def full_path_segments(d, base_dir, longname_field='longname'):
    """Return the full, unambiguous list of path segments that points to an
    entity described by a doclet.

    Example: ``['./', 'dir/', 'dir/', 'file.', 'object.', 'object#', 'object']``

    :arg d: The doclet
    :arg base_dir: Absolutized value of the root_for_relative_js_paths option
    :arg longname_field: The field to look in at the top level of the doclet
        for the long name of the object to emit a path to
    """
    meta = d['meta']
    rel = relpath(meta['path'], base_dir)
    rel = '/'.join(rel.split(sep))
    rooted_rel = rel if is_explicitly_rooted(rel) else './%s' % rel

    # Building up a string and then parsing it back down again is probably
    # not the fastest approach, but it means knowledge of path format is in
    # one place: the parser.
    path = '%s/%s.%s' % (rooted_rel,
                         splitext(meta['filename'])[0],
                         d[longname_field])
    return PathVisitor().visit(
        path_and_formal_params['path'].parse(path))


@cache_to_file(lambda cache, *args: cache)
def jsdoc_output(cache, abs_source_paths, base_dir, sphinx_conf_dir, config_path=None):
    command = Command('jsdoc')
    command.add('-X', *abs_source_paths)
    if config_path:
        command.add('-c', normpath(join(sphinx_conf_dir, config_path)))

    # Use a temporary file to handle large output volume. JSDoc defaults to
    # utf8-encoded output.
    with getwriter('utf-8')(TemporaryFile(mode='w+b')) as temp:
        try:
            p = subprocess.Popen(command.make(), cwd=sphinx_conf_dir, stdout=temp)
        except OSError as exc:
            if exc.errno == ENOENT:
                raise SphinxError('%s was not found. Install it using "npm install -g jsdoc".' % command.program)
            else:
                raise
        p.wait()
        # Once output is finished, move back to beginning of file and load it:
        temp.seek(0)
        try:
            return load(getreader('utf-8')(temp))
        except ValueError:
            raise SphinxError('jsdoc found no JS files in the directories %s. Make sure js_source_path is set correctly in conf.py. It is also possible (though unlikely) that jsdoc emitted invalid JSON.' % abs_source_paths)


def format_default_according_to_type_hints(value, declared_types, first_type_is_string):
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
    :arg first_type_is_string: Whether the first declared type for this param
        is string, which we use as a signal that any string-typed default value
        in the JSON is legitimately string-typed rather than some arrow
        function or something just encased in quotes because they couldn't
        think what else to do. Thus, if you want your ambiguously documented
        default like ``@param {string|Array} [foo=[]]`` to be treated as a
        string, make sure "string" comes first.

    """
    if isinstance(value, str):  # JSDoc threw it to us as a string in the JSON.
        if declared_types and not first_type_is_string:
            # It's a spurious string, like ``() => 5`` or a variable name.
            # Let it through verbatim.
            return value
        else:
            # It's a real string.
            return dumps(value)  # Escape any contained quotes.
    else:  # It came in as a non-string.
        if first_type_is_string:
            # It came in as an int, null, or bool, and we have to
            # convert it back to a string.
            return '"%s"' % (dumps(value),)
        else:
            # It's fine as the type it is.
            return dumps(value)


def description(obj):
    return obj.get('description', '')


def get_type(props):
    """Given an arbitrary object from a jsdoc-emitted JSON file, go get the
    ``type`` property, and return the textual rendering of the type, possibly a
    union like ``Foo | Bar``, or None if we don't know the type."""
    names = props.get('type', {}).get('names', [])
    return '|'.join(names) if names else None


def top_level_properties(doclet, full_path):
    """Extract information common to complex entities, and return it as a dict.

    Specifically, pull out the information needed to parametrize TopLevel's
    constructor.

    """
    return dict(
        name=doclet['name'],
        path=Pathname(full_path),
        filename=doclet['meta']['filename'],
        # description's source varies depending on whether the doclet is a
        #    class, so it gets filled out elsewhere.
        line=doclet['meta']['lineno'],
        deprecated=doclet.get('deprecated', False),
        examples=doclet.get('examples', []),
        see_alsos=doclet.get('see', []),
        properties=properties_to_ir(doclet.get('properties', [])))


def properties_to_ir(properties):
    """Turn jsdoc-emitted properties JSON into a list of Properties."""
    return [Attribute(type=get_type(p),
                      name=p['name'],
                      # We can get away with setting null values for these
                      # because we never use them for anything:
                      path=Pathname([]),
                      filename='',
                      description=description(p),
                      line=0,
                      deprecated=False,
                      examples=[],
                      see_alsos=[],
                      properties=[],
                      exported_from=None,
                      is_abstract=False,
                      is_optional=False,
                      is_static=False,
                      is_private=False)
            for p in properties]


def first_type_is_string(type):
    type_names = type.get('names', [])
    return type_names and type_names[0] == 'string'


def params_to_ir(doclet):
    """Extract the parameters of a function or class, and return a list of
    Param instances.

    Formal param fallback philosophy:

    1. If the user puts a formal param list in the RST explicitly, use that.
    2. Else, if they've @param'd anything, show just those args. This gives the
       user full control from the code, so they can use autoclass without
       having to manually write each function signature in the RST.
    3. Else, extract a formal param list from the meta field, which will lack
       descriptions.

    Param list:

    * Don't show anything without a description or at least a type. It adds
      nothing.

    Our extraction to IR thus follows our formal param philosophy, and the
    renderer caps it off by checking for descriptions and types while building
    the param+description list.

    :arg doclet: A JSDoc doclet representing a function or class

    """
    ret = []

    # First, go through the explicitly documented params:
    for p in doclet.get('params', []):
        type = get_type(p)
        default = p.get('defaultvalue', NO_DEFAULT)
        formatted_default = (
            'dummy' if default is NO_DEFAULT else
            format_default_according_to_type_hints(
                default,
                type,
                first_type_is_string(p.get('type', {}))))
        ret.append(Param(
            name=p['name'],
            description=description(p),
            has_default=default is not NO_DEFAULT,
            default=formatted_default,
            is_variadic=p.get('variable', False),
            type=get_type(p)))

    # Use params from JS code if there are no documented @params.
    if not ret:
        ret = [Param(name=p) for p in
               doclet['meta']['code'].get('paramnames', [])]

    return ret


def exceptions_to_ir(exceptions):
    """Turn jsdoc's JSON-formatted exceptions into a list of Exceptions."""
    return [Exc(type=get_type(e),
                description=description(e))
            for e in exceptions]


def returns_to_ir(returns):
    return [Return(type=get_type(r),
                   description=description(r))
            for r in returns]
