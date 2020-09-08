"""Converter from TypeDoc output to IR format"""

from codecs import getreader
from errno import ENOENT
from json import load
from os.path import basename, join, normpath, relpath, sep, splitext
import re
import subprocess
from tempfile import NamedTemporaryFile
from typing import List, Optional, Tuple, Union

from sphinx.errors import SphinxError

from .analyzer_utils import Command, is_explicitly_rooted
from .ir import Attribute, Class, Function, Interface, NO_DEFAULT, Param, Pathname, Return, TopLevel
from .suffix_tree import SuffixTree


class Analyzer:
    def __init__(self, json, base_dir):
        """
        :arg json: The loaded JSON output from typedoc
        :arg base_dir: The absolute path of the dir relative to which to
            construct file-path segments of object paths

        """
        self._base_dir = base_dir
        self._index = index_by_id({}, json)
        ir_objects = self._convert_all_nodes(json)
        # Toss this overboard to save RAM. We're done with it now:
        del self._index
        self._objects_by_path = SuffixTree()
        self._objects_by_path.add_many((obj.path.segments, obj) for obj in ir_objects)

    @classmethod
    def from_disk(cls, abs_source_paths, app, base_dir):
        json = typedoc_output(abs_source_paths,
                              app.confdir,
                              app.config.jsdoc_config_path)
        return cls(json, base_dir)

    def get_object(self, path_suffix, as_type=None):
        """Return the IR object with the given path suffix.

        :arg as_type: Ignored

        Well, we can't scan through the raw TypeDoc output at runtime, because it's just a linear list of files, each containing a linear list of nodes. They're not indexed at all. And since we need to index by suffix, we need to traverse all the way down, eagerly. Also, we will keep the flattening, because we need it to resolve the IDs of references. (Some of the references are potentially important in the future: that's how TypeDoc points to superclass definitions of methods inherited by subclasses.

        """
        return self._objects_by_path.get(path_suffix)

    def _containing_module(self, node) -> Optional[Pathname]:
        """Return the Pathname pointing to the module containing the given
        node, None if one isn't found."""
        while True:
            node = node.get('__parent')
            if not node or node['id'] == 0:
                # We went all the way up but didn't find a containing module.
                return
            elif node.get('kindString') == 'External module':
                # Found one!
                return Pathname(make_path_segments(node, self._base_dir))

    def _top_level_properties(self, node):
        source = node.get('sources')[0]
        if node.get('flags', {}).get('isExported', False):
            exported_from = self._containing_module(node)
        else:
            exported_from = None
        return dict(
            name=short_name(node),
            path=Pathname(make_path_segments(node, self._base_dir)),
            filename=basename(source['fileName']),
            description=make_description(node.get('comment', {})),
            line=source['line'],

            # These properties aren't supported by TypeDoc:
            deprecated=False,
            examples=[],
            see_alsos=[],
            properties=[],

            exported_from=exported_from)

    def _constructor_and_members(self, cls) -> Tuple[Optional[Function], List[Union[Function, Attribute]]]:
        """Return the constructor and other members of a class.

        In TS, a constructor may have multiple (overloaded) type signatures but
        only one implementation. (Same with functions.) So there's at most 1
        constructor to return. Return None for the constructor if it is inherited
        or implied rather than explicitly present in the class.

        :arg cls: A TypeDoc node of the class to take apart
        :return: A tuple of (constructor Function, list of other members)

        """
        constructor = None
        members = []
        for child in cls.get('children', []):
            ir, _ = self._convert_node(child)
            if ir:
                if (child.get('kindString') == 'Constructor'):
                    # This really, really should happen exactly once per class.
                    constructor = ir
                else:
                    members.append(ir)
        return constructor, members

    def _convert_all_nodes(self, root):
        todo = [root]
        done = []
        while todo:
            converted, more_todo = self._convert_node(todo.pop())
            if converted:
                done.append(converted)
            todo.extend(more_todo)
        return done

    def _convert_node(self, node) -> Tuple[TopLevel, List[dict]]:
        """Convert a node of TypeScript JSON output to an IR object.

        :return: A tuple: (the IR object, a list of other nodes found within
            that you can convert to other IR objects). For the second item of
            the tuple, nodes that can't presently be converted to IR objects
            are omitted.

        """
        if node.get('inheritedFrom'):
            return None, []
        if node.get('sources'):
            # Ignore nodes with a reference to absolute paths (like /usr/lib)
            source = node.get('sources')[0]
            if source.get('fileName', '.')[0] == '/':
                return None, []

        ir = None
        kind = node.get('kindString')
        if kind == 'External module':
            # We shouldn't need these until we implement automodule. But what of
            # js:mod in the templates?
            pass
        elif kind == 'Module':
            # Does anybody even use TS's old internal modules anymore?
            pass
        elif kind == 'Interface':
            _, members = self._constructor_and_members(node)
            ir = Interface(
                members=members,
                supers=self._related_types(node, kind='extendedTypes'),
                **self._top_level_properties(node))
        elif kind == 'Class':
            # Every class has a constructor in the JSON, even if it's only
            # inherited.
            constructor, members = self._constructor_and_members(node)
            ir = Class(
                constructor=constructor,
                members=members,
                supers=self._related_types(node, kind='extendedTypes'),
                is_abstract=node.get('flags', {}).get('isAbstract', False),
                interfaces=self._related_types(node, kind='implementedTypes'),
                **self._top_level_properties(node))
        elif kind in ['Property', 'Variable']:
            ir = Attribute(
                type=self._type_name(node.get('type')),
                **member_properties(node),
                **self._top_level_properties(node))
        elif kind == 'Accessor':  # NEXT: Write renderers.
            get_signature = node.get('getSignature')
            if get_signature:
                # There's no signature to speak of for a getter: only a return type.
                type = get_signature[0]['type']
            else:
                # ES6 says setters have exactly 1 param. I'm not sure if they can
                # have multiple signatures, though.
                type = node['setSignature'][0]['parameters'][0]['type']
            ir = Attribute(
                type=self._type_name(type),
                **member_properties(node),
                **self._top_level_properties(node))
        elif kind in ['Function', 'Constructor', 'Method']:
            # There's really nothing in these; all the interesting bits are in the
            # contained 'Call signature' keys. We support only the first signature
            # at the moment, because to do otherwise would create multiple
            # identical pathnames to the same function, which would cause the
            # suffix tree to raise an exception while being built. An eventual
            # solution might be to store the signatures in a one-to-many attr of
            # Functions.
            sigs = node.get('signatures')
            first_sig = sigs[0]  # Should always have at least one
            first_sig['sources'] = node['sources']
            return self._convert_node(first_sig)
        elif kind in ['Call signature', 'Constructor signature']:
            # This is the real meat of a function, method, or constructor.
            #
            # Constructors' .name attrs end up being like 'new Foo'. They
            # should probably be called "constructor", but I'm not bothering
            # with that yet because nobody uses that attr on constructors atm.
            ir = Function(
                params=[self._make_param(p) for p in node.get('parameters', [])],
                # Exceptions are discouraged in TS as being unrepresentable in its
                # type system. More importantly, TypeDoc does not support them.
                exceptions=[],
                # Though perhaps technically true, it looks weird to the user
                # (and in the template) if constructors have a return value:
                returns=self._make_returns(node) if kind != 'Constructor signature' else [],
                **member_properties(node['__parent']),
                **self._top_level_properties(node))

        return ir, node.get('children', [])

    def _related_types(self, node, kind):
        """Return the unambiguous pathnames of implemented interfaces or
        extended classes.

        If we encounter a formulation of interface or class reference that we
        don't understand (which I expect to occur only if it turns out you can
        use a class or interface literal rather than referencing a declared
        one), return 'UNIMPLEMENTED' for that interface or class so somebody
        files a bug requesting we fix it. (It's not worth crashing for.)

        """
        types = []
        for type in node.get(kind, []):
            if type['type'] == 'reference':
                pathname = Pathname(make_path_segments(self._index[type['id']],
                                                       self._base_dir))
                types.append(pathname)
            # else it's some other thing we should go implement
        return types

    def _type_name(self, type):
        """Return a string description of a type.

        :arg type: A TypeDoc-emitted type node

        """
        type_of_type = type.get('type')

        if type_of_type == 'reference' and type.get('id'):
            node = self._index[type['id']]
            name = node['name']
        elif type_of_type == 'unknown':
            if re.match(r'-?\d*(\.\d+)?', type['name']):  # It's a number.
                # TypeDoc apparently sticks numeric constants' values into the
                # type name. String constants? Nope. Function ones? Nope.
                name = 'number'
            else:
                name = type['name']
        elif type_of_type in ['intrinsic', 'reference']:
            name = type['name']
        elif type_of_type == 'stringLiteral':
            name = '"' + type['value'] + '"'
        elif type_of_type == 'array':
            name = self._type_name(type['elementType']) + '[]'
        elif type_of_type == 'tuple' and type.get('elements'):
            types = [self._type_name(t) for t in type['elements']]
            name = '[' + ', '.join(types) + ']'
        elif type_of_type == 'union':
            name = '|'.join(self._type_name(t) for t in type['types'])
        elif type_of_type == 'intersection':
            name = ' & '.join(self._type_name(t) for t in type['types'])
        elif type_of_type == 'typeOperator':
            name = type['operator'] + ' ' + self._type_name(type['target'])
            # e.g. "keyof T"
        elif type_of_type == 'typeParameter':
            name = type['name']
            constraint = type.get('constraint')
            if constraint is not None:
                name += ' extends ' + self._type_name(constraint)
                # e.g. K += extends + keyof T
        elif type_of_type == 'reflection':
            name = '<TODO: reflection>'
            # test_generic_member() (currently skipped) tests this.
        else:
            name = '<TODO: other type>'

        type_args = type.get('typeArguments')
        if type_args:
            arg_names = ', '.join(self._type_name(arg) for arg in type_args)
            name += f'<{arg_names}>'

        return name

    def _make_param(self, param):
        """Make a Param from a 'parameters' JSON item"""
        has_default = 'defaultValue' in param
        return Param(
            name=param.get('name'),
            description=make_description(param.get('comment', {})),
            has_default=has_default,
            is_variadic=param.get('flags', {}).get('isRest', False),
            # For now, we just pass a single string in as the type rather than a
            # list of types to be unioned by the renderer. There's really no
            # disadvantage.
            type=self._type_name(param.get('type', {})),
            default=param['defaultValue'] if has_default else NO_DEFAULT)

    def _make_returns(self, signature) -> List[Return]:
        """Return the Returns a function signature can have.

        Because, in TypeDoc, each signature can have only 1 @return tag, we return
        a list of either 0 or 1 item.

        """
        type = signature.get('type')
        if type is None or type.get('name') == 'void':
            # Returns nothing
            return []
        return [Return(
            type=self._type_name(type),
            description=signature.get('comment', {}).get('returns', '').strip())]


def typedoc_output(abs_source_paths, sphinx_conf_dir, config_path):
    """Return the loaded JSON output of the TypeDoc command run over the given
    paths."""
    command = Command('typedoc')
    if config_path:
        command.add('--tsconfig', normpath(join(sphinx_conf_dir, config_path)))

    with NamedTemporaryFile(mode='w+b') as temp:
        command.add('--json', temp.name, *abs_source_paths)
        try:
            subprocess.call(command.make())
        except OSError as exc:
            if exc.errno == ENOENT:
                raise SphinxError('%s was not found. Install it using "npm install -g typedoc".' % command.program)
            else:
                raise
        # typedoc emits a valid JSON file even if it finds no TS files in the dir:
        return load(getreader('utf-8')(temp))


def index_by_id(index, node, parent=None):
    """Create an ID-to-node mapping for all the TypeDoc output nodes.

    We don't unnest them, but we do add ``__parent`` keys so we can easily walk
    both up and down.

    :arg index: The mapping to add keys to as we go
    :arg node: The node to start traversing down from
    :arg parent: The parent node of ``node``

    """
    # TODO: Can we just uniformly set __parent on nodes rather than doing it
    # differently in different cases? I think the reason for the cases is that
    # we used to set a parent ID rather than a parent pointer and not all nodes
    # have IDs.
    if node is not None:
        id = node.get('id')
        if id is not None:  # 0 is okay; it's the root node.
            # Give anything in the map a parent:
            node['__parent'] = parent  # Parents are used for (1) building longnames, (2) setting memberof (which we shouldn't have to do anymore; we can just traverse children), (3) getting the module a class or interface is defined in so we can link to it, and (4) one other things, so it's worth setting them.
            index[id] = node

        # Burrow into everything that could contain more ID'd items. We don't
        # need setSignature or getSignature for now. Do we need indexSignature?
        for tag in ['children', 'signatures', 'parameters']:
            for child in node.get(tag, []):
                index_by_id(index, child, parent=node)

        return index


def make_description(comment):
    """Construct a single comment string from a fancy object."""
    ret = '\n\n'.join(text for text in [comment.get('shortText'),
                                        comment.get('text')]
                      if text)
    return ret.strip()


def member_properties(node):
    flags = node.get('flags', {})
    return dict(
        is_abstract=flags.get('isAbstract', False),
        is_optional=flags.get('isOptional', False),
        is_static=flags.get('isStatic', False),
        is_private=flags.get('isPrivate', False))


def short_name(node):
    if node['kindString'] in ['Module', 'External module']:
        return node['name'][1:-1]  # strip quotes
    return node['name']


# Optimization: Could memoize this for probably a decent perf gain: every child
# of an object redoes th work for all its parents.
def make_path_segments(node, base_dir, child_was_static=None):
    """Return the full, unambiguous list of path segments that points to an
    entity described by a TypeDoc JSON node.

    Example: ``['./', 'dir/', 'dir/', 'file.', 'object.', 'object#', 'object']``

    :arg base_dir: Absolute path of the dir relative to which file-path
        segments are constructed
    :arg child_was_static: True if the child node we're computing the path of
        is a static member of the node under consideration. False if it is.
        None if the current node is the one we're ultimately computing the path
        of.

    TypeDoc uses a totally different, locality-sensitive resolution mechanism
    for links: https://typedoc.org/guides/link-resolution/. It seems like a
    less well thought-out system than JSDoc's namepaths, as it doesn't
    distinguish between, say, static and instance properties of the same name.
    (AFAICT, TypeDoc does not emit documentation for inner properties, as for a
    function nested within another function.) We're sticking with our own
    namepath-like paths, even if we eventually support {@link} syntax.

    """
    node_is_static = node.get('flags', {}).get('isStatic', False)

    parent = node.get('__parent')
    parent_segments = (make_path_segments(parent, base_dir, child_was_static=node_is_static)
                       if parent else [])

    kind = node.get('kindString')
    delimiter = '' if child_was_static is None else '.'

    # Handle the cases here that are handled in _convert_node(), plus any that
    # are encountered on other nodes on the way up to the root.
    if kind in ['Variable', 'Property', 'Accessor', 'Interface', 'Module']:
        # We emit a segment for a Method's child Call Signature but skip the
        # Method itself. They 2 nodes have the same names, but, by taking the
        # child, we fortuitously end up without a trailing delimiter on our
        # last segment.
        segments = [node['name']]
    elif kind in ['Call signature', 'Constructor signature']:
        # Similar to above, we skip the parent Constructor and glom onto the
        # Constructor Signature. That gets us no trailing delimiter. However,
        # the signature has name == 'new Foo', so we go up to the parent to get
        # the real name, which is usually (always?) "constructor".
        segments = [parent['name']]
    elif kind == 'Class':
        segments = [node['name']]
        if child_was_static is False:
            delimiter = '#'
    elif kind == 'External module':
        # 'name' contains folder names if multiple folders are passed into
        # TypeDoc. It's also got excess quotes. So we ignore it and take
        # 'originalName', which has a nice, absolute path.
        rel = relpath(node['originalName'], base_dir)
        if not is_explicitly_rooted(rel):
            rel = f'.{sep}{rel}'
        segments = rel.split(sep)
        filename = splitext(segments[-1])[0]
        segments = [s + '/' for s in segments[:-1]] + [filename]
    else:
        # None, as for a root node, Constructor, or Method
        segments = []

    if segments:
        # It's not some abstract thing the user doesn't think about and we skip
        # over.
        segments[-1] += delimiter
        return parent_segments + segments
    else:
        # Allow some levels of the JSON to not have a corresponding path segment:
        return parent_segments
