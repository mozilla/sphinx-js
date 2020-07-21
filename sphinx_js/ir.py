"""Intermediate representation that JS and TypeScript are transformed to for
use by the rest of sphinx-js

This results from my former inability to review any but the most trivial
TypeScript PRs due to jsdoc's JSON output format being undocumented, often
surprising, and occasionally changing.

This IR is not intended to be a lossless representation of either jsdoc's or
typedoc's output. Nor is it meant to generalize to other uses like static
analysis. Ideally, it exists to provide the minimum information necessary to
render our Sphinx templates about JS and TS entities. Any expansion or
generalization of the IR should be driven by needs of those templates and the
minimal logic around them. The complexity of doing otherwise has no payback.

I was conflicted about introducing an additional representation, since a
multiplicity of representations incur conversion complexity costs at a
superlinear rate. However, I think it is essential complexity here. The
potentially simpler approach would have been to have the RST template vars
required by our handful of directives be the IR. However, we still would have
wanted to factor out formatting like the joining of types with "|" and the
unwrapping of comments, making another representation inevitable. Therefore,
let's at least have a well-documented one and one slightly more likely to
survive template changes.

"""
from dataclasses import dataclass, field, InitVar
from typing import Any, List, Union


#: List of types, which are strings. Types could even be parametrized by
#: other types, but we probably don't care for IR purposes: let whichever
#: analyzer boil them down to strings.
Types = List[str]


@dataclass
class Property:
    name: str
    types: Types
    description: str


class NoDefault:
    """A conspicuous no-default value that will show up in templates to help
    troubleshoot code paths that grab ``Param.default`` without checking
    ``Param.has_default`` first."""
    def __repr__(self):
        return '<no default value>'
NO_DEFAULT = NoDefault()


@dataclass
class Param:
    """A parameter of either a function or (in the case of TS, which has
    classes parametrized by type) a class."""
    name: str
    description: str = ''
    has_default: bool = False
    is_variadic: bool = False
    types: Types = field(default_factory=list)
    #: Return the default value of this parameter, string-formatted so it can
    #: be immediately suffixed to an equal sign in a formal param list. For
    #: example, the number 6 becomes the string "6" to create ``foo="6"``. If
    #: has_default=True, this must be set.
    default: InitVar[Any] = NO_DEFAULT

    def __post_init__(self, default):
        if self.has_default and default is NO_DEFAULT:
            raise ValueError('Tried to construct a Param with has_default=True but without `default` specified.')
        self.default = default


@dataclass
class Exc:
    """A declaration of one kind of exception that can be raised"""
    #: The type of types the exception can have
    types: Types
    description: str


@dataclass
class Return:
    """One kind of thing a function can return"""
    types: Types
    description: str


@dataclass
class TopLevel:
    """A JavaScript or TypeScript object you can look up by path

    The semantics on this are fuzzy, but I feel like it's also a complex
    entity. Obviously, it's at least the sort of thing with the potential to
    include the kinds of subentities referenced by these fields.

    """
    # TODO: See if name is always the last item of path_segments. If so, don't make them pass name in.
    #: The short name of the object, regardless of whether it's a class or
    #: function or typedef or param
    name: str
    #: The namepath-like unambiguous identifier of the object, e.g. ``['./',
    #: 'dir/', 'dir/', 'file/', 'object.', 'object#', 'object']``
    path_segments: List[str]
    #: The basename of the file the object is from, e.g. "foo.js"
    filename: str
    #: The human-readable description of the entity or '' if absent
    description: str
    #: Line number where the object (exluding any prefixing comment) begins
    line: int
    #: String explanation of the deprecation (which implies True) or True or False
    deprecated: Union[str, bool]
    #: List of preformatted textual examples
    examples: List[str]
    #: List of paths to also refer the reader to
    see_alsos: List[str]
    #: Explicitly documented sub-properties of the object, a la jsdoc's @properties
    properties: List[Property]
    is_private: bool


@dataclass
class Attribute(TopLevel):
    types: Types


@dataclass
class Function(TopLevel):
    params: List[Param]
    exceptions: List[Exc]
    returns: List[Return]


@dataclass
class Class(TopLevel):
    #: The default constructor for this class
    constructor: Function
    #: Class members, concretized ahead of time for simplicity. Otherwise,
    #: we'd have to pass the doclets_by_class map in and keep it around, along
    #: with a callable that would create the member IRs from it on demand.
    members: List[Union[Function, Attribute]]
    # There's room here for additional fields like @example on the class doclet
    # itself. These are supported and extracted by jsdoc, but they end up in an
    # `undocumented: True` doclet and so are presently filtered out. But we do
    # have the space to include them later.
