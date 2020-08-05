"""Converter from typedoc output to jsdoc doclet format"""

from codecs import getreader
from errno import ENOENT
from json import load
from os.path import join, normpath
import subprocess
from tempfile import NamedTemporaryFile
from typing import List, Tuple, Union

from sphinx.errors import SphinxError

from .analyzer_utils import Command
from .ir import Attribute, Class, Exc, Function, Interface, Param, Return, TopLevel, Types


class Analyzer:
    def __init__(self, json, base_dir):
        """
        :arg json: The loaded JSON output from typedoc
        :arg base_dir: The absolute path of the dir relative to which to
            construct object paths

        """
        index = index_by_id({}, json)
        ir_nodes = []
        # Maybe index them into the suffix tree as we go, yielding from convert_all_nodes?
        convert_all_nodes(json, index)
        # self._objects_by_path = SuffixTree()
        # and index ir_nodes by suffix.

    @classmethod
    def from_disk(cls, abs_source_paths, app, base_dir):
        json = typedoc_output(abs_source_paths,
                              base_dir,
                              app.confdir,
                              app.config.jsdoc_config_path)
        return cls(json, base_dir)

    def get_object(self, path_suffix, as_type=None):
        """Return the IR object with the given path suffix.

        :arg as_type: Ignored

        Well, we can't scan through the raw TypeDoc output at runtime, because it's just a linear list of files, each containing a linear list of nodes. They're not indexed at all. And since we need to index by suffix, we need to traverse all the way down, eagerly. Also, we will keep the flattening, because we need it to resolve the IDs of references. (Some of the references are potentially important in the future: that's how TypeDoc points to superclass definitions of methods inherited by subclasses.

        """

        doclet, full_path = self.doclets_by_path.get_with_path(path_suffix)
        return doclet_as_whatever(doclet, full_path)


def typedoc_output(abs_source_paths, base_dir, sphinx_conf_dir, config_path):
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
    # TODO: Can we just uniformly set __parent on nodes rather than doing it differently in different cases? I think the reason for the cases is that we used to set a parent ID rather than a parent pointer and not all nodes have IDs.
    if node is not None:
        id = node.get('id')
        if id is not None:  # 0 is okay; it's the root node.
            # Give anything in the map a parent:
            node['__parent'] = parent  # Parents are used for (1) building longnames, (2) setting memberof (which we shouldn't have to do anymore; we can just traverse children), (3) getting the module a class or interface is defined in so we can link to it, and (4) one other things, so it's worth setting them.
            index[id] = node

        # Burrow into everything that could contain more ID'd items:
        for tag in ['children', 'signatures', 'parameters']:  # TODO: Add setSignature, probably. And getSignature. Do we need indexSignature?
            for child in node.get(tag, []):
                index_by_id(index, child, parent=node)

        return index

        # Index type declarations:
#         type = node.get('type')
#         if isinstance(type, dict) and type['type'] != 'reference':
#             # index_by_id(index, type, parent=node)  # I don't think any non-reference type has an ID, so this never does anything.
#             # I found these only in "type" properties:
#             index_by_id(index, node.get('declaration'), parent=None)  # Seems like this should be parent=parent, since "type" properties never have seem to have IDs.  # Further, I don't see what good assigning any parent here does, since make_type_name() doesn't implement reference types yet.


def make_description(comment):
    """Construct a single comment string from a fancy object."""
    return '\n\n'.join(text for text in [comment.get('shortText'),
                                         comment.get('text')]
                       if text)


def top_level_properties(node):
    source = node.get('sources')[0]
    if node.get('flags', {}).get('isExported', False):
        exported_from = node['__parent']['name'][1:-1]  # strip off quotes
    else:
        exported_from = None
    return dict(
        name=short_name(node),
        path_segments=make_path_segments(node),
        filename=os.path.basename(source['fileName']),
        description=make_description(node.get('comment', {})),
        line=source['line'],
        is_private=node.get('flags', {}).get('isPrivate', False),
        exported_from=exported_from)


def short_name(node):
    if node['kindString'] in ['Module', 'External module']:
        return node['name'][1:-1]  # strip quotes
    return node['name']


def constructor_and_members(cls) -> Tuple[Function, List[Union[Function, Attribute]]]:
    """Return the constructor and other members of a class.

    In TS, a constructor may have multiple (overlaoded) type signatures but
    only one implementation. (Same with functions.) So there's only 1
    constructor to return.

    :arg cls: A TypeDoc node of the class to take apart
    :return: A tuple of (constructor Function, list of other members)

    """
    members = []
    for child in cls.get('children', []):
        ir = convert_node(child)
        if ir:
            if (child.get('kindString') == 'Constructor'):
                # This really, really should happen exactly once per class.
                constructor = ir
            else:
                members.append(ir)
    return constructor, members


def related_types(node, kind):
    """Return the names of implemented or extended classes or interfaces or maybe paths to them. I'm not sure."""
    types = []
    for type in node.get(kind, []):
        types.append(' '.join(make_type_name(type)))
    return types


def convert_all_nodes(root, index):
    todo = [root]
    done = []
    while todo:
        converted, more_todo = convert_node(todo.pop(), index)
        if converted:
            done.append(converted)
        todo.extend(more_todo)
    return done


# TODO: Unit-test me.
def make_type(type, index) -> Types:
    """Construct a list of types from a TypeDoc ``type`` entry.

    Return a list of 1 type, or [] if none is specified.

    """
    names = []
    type_of_type = type.get('type')
    if type_of_type == 'reference' and type.get('id'):
        node = index[type['id']]
        # Should be: names = [ self.make_longname(node)]
        parent = node['__parent']
        if parent.get('kindString') == 'External module':
            names = [parent['name'][1:-1] + '.' + node['name']]
        else:
            names = [node['name']]
    elif type_of_type in ['intrinsic', 'reference', 'unknown']:
        names = [type['name']]
    elif type_of_type == 'stringLiteral':
        names = ['"' + type['value'] + '"']
    elif type_of_type == 'array':
        names = [make_type(type['elementType'])[0] + '[]']
    elif type_of_type == 'tuple' and type.get('elements'):
        types = ['|'.join(make_type(t)) for t in type['elements']]
        names = ['[' + ','.join(types) + ']']
    elif type_of_type == 'union':
        types = []
        for t in type['types']:
            mt = make_type(t)
            if mt:  # Avoid []s (untyped things)
                types.append(mt)
        names = ['|'.join(types)]
    elif type_of_type == 'typeOperator':
        target_name = make_type(type['target'])
        names = [type['operator'] + ':' + ':'.join(target_name)]
    elif type_of_type == 'typeParameter':
        names = [type['name']]
        constraint = type.get('constraint')
        if constraint is not None:
            names.extend(['extends', make_type(constraint)])  # TODO: Longer list than we want. Join it with spaces?
    elif type_of_type == 'reflection':
        names = ['<TODO>']

    type_args = type.get('typeArguments')
    if type_args:
        arg_names = ['|'.join(make_type(arg)) for arg in type_args]
        names = [names[0] + '<' + ','.join(arg_names) + '>']

    return names


def make_param(param):
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
        types=make_type(param.get('type', {})),
        default=param['defaultValue'] if has_default else NO_DEFAULT)


def make_returns(signature) -> List[Return]:
    """Return the Returns a function signature can have.

    Because, in TypeDoc, each signature can have only 1 @return tag, we return
    a list of either 0 or 1 item.

    """
    type = signature.get('type')
    if type is None or type.get('name') == 'void':
        # Returns nothing
        return []
    return [Return(
        types=make_type(type),
        description=signature.get('comment', {}).get('returns', ''))]


# Optimization: Could memoize this for probably a decent perf gain: every child
# of an object redoes th work for all its parents.
def make_path_segments(node, base_dir, child_was_static=None):
    """Return the full, unambiguous list of path segments that points to an
    entity described by a TypeDoc JSON node.

    Example: ``['./', 'dir/', 'dir/', 'file.', 'object.', 'object#', 'object']``

    Emitted file-path segments are relative to ``base_dir``.

    :arg child_was_static: True if the child node we're computing the path of
        is a static member of the node under consideration. False if it is.
        None if the current node is the one we're ultimately computing the path
        of.

    """
    # TODO: Make sure this works with properties that contain reserved chars like #.~.
    try:
        node_is_static = node.get('flags', {}).get('isStatic', False)
    except AttributeError as e:
        import pdb;pdb.set_trace()

    parent = node.get('__parent')
    parent_segments = (make_path_segments(parent, base_dir, child_was_static=node_is_static)
                       if parent else [])

    kind = node.get('kindString')
    # TODO: See if the '~' (inner property) case ever fired on the old version of sphinx-js. I don't think TypeDoc emits inner properties.
    delimiter = '' if child_was_static is None else '.'
    # cases to handle: accessor, Call signature, Constructor signature, method
    # + any that occur between those and the file node.
    segment = ''
    # Handle the cases here that are handled in convert_node(), plus any that
    # are encountered on other nodes on the way up to the root.
    if kind in ['Function', 'Constructor', 'Method', 'Property', 'Accessor', 'Interface']:
        segment = node['name']
    elif kind == 'Class':
        segment = node['name']
        if child_was_static == False:  # Interface members are always static.
            delimiter = '#'
    elif kind == 'Module':
        # TODO: Figure this out. Does it have filenames to relativize like external modules?
        segment = node.get('name')[1:-1]
    elif kind == 'External module':
        # 'name' key contains folder names, starting from the root passed to
        # TypeDoc, e.g. 'more/stuff.ts' if you pass it 'more'. When passed
        # multiple source folders to scan, typedoc's 'name' keys for the
        # external modules start just inside the deepest common folder of all
        # the source folders. For example, if you pass a/b/c/d and a/b/e/f, the
        # paths in the JSON will be c/d/... and e/f/.... Thus, we'll have to
        # look at the 'originalName' keys, relativize relative to our
        # root_for_relative_js_paths, and go from there.
        # TODO: Relativize.
        segment = node.get('name')[1:-1]
    else:
        # None, as for the root node
        pass

    if segment:
        # It's not some abstract thing the user doesn't think about and we skip
        # over.
        segment += delimiter
        return parent_segments + [segment]
    else:
        # Allow some levels of the JSON to not have a corresponding path segment:
        return parent_segments
    # TODO: Take into account FS paths. Right now, we'd just starting with
    # whatever TS's concept of modules is. I don't know if that takes into
    # account FS paths (it does: it's all about relative paths), especially in multi-item js_source_path configurations
    # that might lead to module name collisions. OTOH, TypeDoc uses a totally
    # different, locality-sensitive resolution mechanism for links:
    # https://typedoc.org/guides/link-resolution/. It seems like a less well
    # thought-out system than JSDoc's namepaths, as it doesn't distinguish
    # between, say, static and instance properties. I'm leaning toward
    # requiring our own namepath-like paths, even if we eventually support
    # {@link} syntax.

def convert_node(node, index) -> Tuple[TopLevel, List[dict]]:
    """Convert a node of TypeScript JSON output to an IR object.

    :return: A tuple: (the IR object, a list of other nodes found within that
        you can convert to other IR objects). For the second item of the tuple,
        nodes that can't presently be converted to IR objects are omitted.

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
        _, members = constructor_and_members(node)
        ir = Interface(
            members=members,
            supers=related_types(node, kind='extendedTypes'),
            **top_level_properties(node))
    elif kind == 'Class':
        # Every class has a constructor in the JSON, even if it's only
        # inherited.
        constructor, members = constructor_and_members(node)
        ir = Class(
            constructor=constructor,
            members=members,
            supers=related_types(node, kind='extendedTypes'),
            is_abstract=node.get('flags', {}).get('isAbstract', False),
            interfaces=related_types(node, kind='implementedTypes'),
            **top_level_properties(node))
    elif kind == 'Property':
        ir = Attribute(
            types=make_type(node.get('type')),
            **top_level_properties(node))
    elif kind == 'Accessor':  # NEXT: Then port longname. Then convert_node() should work. Unit-test, especially make_type() and make_longname(). Then write renderers.
        doclet = self.simple_doclet('member', node)
        get_signature = node.get('getSignature')
        if get_signature:
            # There's no signature to speak of for a getter: only a return type.
            type = get_signature[0]['type']
        else:
            # ES6 says setters have exactly 1 param. I'm not sure if they can
            # have multiple signatures, though.
            type = node['setSignature'][0]['parameters'][0]['type']
        ir = Attribute(
            types=make_type(type),
            **top_level_properties(node))
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
        return convert_node(first_sig, index)
    elif kind in ['Call signature', 'Constructor signature']:  # I had deleted "Constructor signature". I don't know why.
        # This is the real meat of a function, method, or constructor.
        parent = node['__parent']
        flags = parent.get('flags', {})
        ir = Function(
            params=[make_param(p) for p in node.get('parameters', [])],
            # Exceptions are discouraged in TS as being unrepresentable in its
            # type system. More importantly, TypeDoc does not support them.
            returns=make_returns(node),
            is_abstract=flags.get('isAbstract', False),
            is_optional=flags.get('isOptional', False),
            is_static=flags.get('isStatic', False),
            **top_level_properties(node))

    return ir, node.get('children', [])

