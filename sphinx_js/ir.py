"""Intermediate representation that JS and TypeScript are transformed to for
use by the rest of sphinx-js

This results from my former inability to review any but the most trivial
TypeScript PRs due to jsdoc's JSON output format being undocumented, often
surprising, and occasionally changing.

This IR is not intended to be a lossless representation of either jsdoc's or
typedoc's output. Nor is it meant to generalize to other uses like static
analysis. Ideally, it provides the minimum information necessary to render our
Sphinx templates about JS and TS entities. Any expansion or generalization of
the IR should be driven by needs of those templates and the (minimal) logic
around them. The complexity of doing otherwise has no payback.

I was conflicted about introducing an additional representation, since a
multiplicity of representations incurs conversion complexity costs at a
superlinear rate. However, I think it is essential complexity here. The
potentially simpler approach would have been to let the RST template vars
required by our handful of directives be the IR. However, we still would have
wanted to factor out formatting like the joining of types with "|" and the
unwrapping of comments, making another representation inevitable. Therefore,
let's at least have a well-documented one and one slightly more likely to
survive template changes.

"""
from dataclasses import dataclass, InitVar
from typing import Any, List, NewType, Optional, Union

from .analyzer_utils import dotted_path


#: Human-readable type of a value. None if we don't know the type.
Type = NewType('Type', Optional[str])
# In the far future, we may take full control of our RST templates rather than
# using the js-domain directives provided by Sphinx. This would give us the
# freedom to link type names in formal param lists and param description lists
# to their definitions. To do this, we could replace the string-based Type with
# a class-based Type which internally preserves the structure of the type
# (simple for JS, fancy for TS) and can, on request, render it out as either
# text or link-having RST.

#: Pathname, full or not, to an object:
ReStructuredText = NewType('ReStructuredText', str)


class Pathname:
    """A partial or full path to a language entity.

    Example: ``['./', 'dir/', 'dir/', 'file.', 'object.', 'object#', 'object']``

    """
    def __init__(self, segments):
        self.segments = segments

    def __str__(self):
        return ''.join(self.segments)

    def __repr__(self):
        return '<Pathname(%r)>' % self.segments

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.segments == other.segments

    def dotted(self):
        return dotted_path(self.segments)


class _NoDefault:
    """A conspicuous no-default value that will show up in templates to help
    troubleshoot code paths that grab ``Param.default`` without checking
    ``Param.has_default`` first."""
    def __repr__(self):
        return '<no default value>'
NO_DEFAULT = _NoDefault()


@dataclass
class _Member:
    """An IR object that is a member of another, as a method is a member of a
    class or interface"""
    #: Whether this member is required to be provided by a subclass of a class
    #: or implementor of an interface
    is_abstract: bool
    #: Whether this member is optional in the TypeScript sense of being allowed
    #: on but not required of an object to conform to a type
    is_optional: bool
    #: Whether this member can be accessed on the container itself rather than
    #: just on instances of it
    is_static: bool
    #: Is a private member of a class or, at least in JSDoc, a @namespace:
    is_private: bool


@dataclass
class Param:
    """A parameter of either a function or (in the case of TS, which has
    classes parametrized by type) a class."""
    name: str
    #: The description text (like all other description fields in the IR)
    #: retains any line breaks and subsequent indentation whitespace that were
    #: in the source code.
    description: ReStructuredText = ''
    has_default: bool = False
    is_variadic: bool = False
    type: Type = None
    #: Return the default value of this parameter, string-formatted so it can
    #: be immediately suffixed to an equal sign in a formal param list. For
    #: example, the number 6 becomes the string "6" to create ``foo=6``. If
    #: has_default=True, this must be set.
    default: InitVar[Any] = NO_DEFAULT  # noqa: flake8 thinks this is a "def".

    def __post_init__(self, default):
        if self.has_default and default is NO_DEFAULT:
            raise ValueError('Tried to construct a Param with has_default=True but without `default` specified.')
        self.default = default


@dataclass
class Exc:
    """One kind of exception that can be raised by a function"""
    #: The type of exception can have
    type: Type
    description: ReStructuredText


@dataclass
class Return:
    """One kind of thing a function can return"""
    #: The type this kind of return value can have
    type: Type
    description: ReStructuredText


@dataclass
class TopLevel:
    """A language object with an independent existence

    A TopLevel entity is a potentially strong entity in the database sense; one
    of these can exist on its own and not merely as a datum attached to another
    entity. For example, Returns do not qualify, since they cannot exist
    without a parent Function. And, though a given Attribute may be attached to
    a Class, Attributes can also exist top-level in a module.

    These are also complex entities: the sorts of thing with the potential to
    include the kinds of subentities referenced by the fields defined herein.

    """
    #: The short name of the object, regardless of whether it's a class or
    #: function or typedef or param.
    #:
    #: This is usually the same as the last item of path.segments but not
    #: always. For example, in JSDoc Attributes defined with @property, name is
    #: defined but path is empty. This was a shortcut and could be corrected at
    #: some point. If it is, we can stop storing name as a separate field. Also
    #: TypeScript constructors are named "new WhateverClass". They should
    #: instead be called "constructor".
    name: str
    #: The namepath-like unambiguous identifier of the object, e.g. ``['./',
    #: 'dir/', 'dir/', 'file/', 'object.', 'object#', 'object']``
    path: Pathname
    #: The basename of the file the object is from, e.g. "foo.js"
    filename: str
    #: The human-readable description of the entity or '' if absent
    description: ReStructuredText
    #: Line number where the object (exluding any prefixing comment) begins
    line: int
    #: Explanation of the deprecation (which implies True) or True or False
    deprecated: Union[ReStructuredText, bool]
    #: List of preformatted textual examples
    examples: List[str]
    #: List of paths to also refer the reader to
    see_alsos: List[str]
    #: Explicitly documented sub-properties of the object, a la jsdoc's @properties
    properties: List['Attribute']
    #: None if not exported for use by outside code. Otherwise, the Sphinx
    #: dotted path to the module it is exported from, e.g. 'foo.bar'
    exported_from: Optional[Pathname]


@dataclass
class Attribute(TopLevel, _Member):
    """A property of an object

    These are called attributes to match up with Sphinx's autoattribute
    directive which is used to display them.

    """
    #: The type this property's value can have
    type: Type


@dataclass
class Function(TopLevel, _Member):
    params: List[Param]
    exceptions: List[Exc]  # noqa: Linter is buggy.
    returns: List[Return]


@dataclass
class _MembersAndSupers:
    """An IR object that can contain members and extend other types"""
    #: Class members, concretized ahead of time for simplicity. (Otherwise,
    #: we'd have to pass the doclets_by_class map in and keep it around, along
    #: with a callable that would create the member IRs from it on demand.)
    #: Does not include the default constructor.
    members: List[Union[Function, Attribute]]
    #: Objects this one extends: for example, superclasses of a class or
    #: superinterfaces of an interface
    supers: List[Pathname]


@dataclass
class Interface(TopLevel, _MembersAndSupers):
    """An interface, a la TypeScript"""


@dataclass
class Class(TopLevel, _MembersAndSupers):
    #: The default constructor for this class. Absent if the constructor is
    #: inherited.
    constructor: Optional[Function]
    #: Whether this is an abstract class
    is_abstract: bool
    #: Interfaces this class implements
    interfaces: List[Pathname]
    # There's room here for additional fields like @example on the class doclet
    # itself. These are supported and extracted by jsdoc, but they end up in an
    # `undocumented: True` doclet and so are presently filtered out. But we do
    # have the space to include them someday.
