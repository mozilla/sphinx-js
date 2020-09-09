from json import loads
from os.path import dirname
from unittest import TestCase

import pytest

from sphinx_js.ir import Attribute, Class, Function, Param, Pathname, Return
from sphinx_js.typedoc import index_by_id, make_path_segments
from tests.testing import dict_where, NO_MATCH, TypeDocAnalyzerTestCase, TypeDocTestCase


class IndexByIdTests(TestCase):
    def test_top_level_function(self):
        """Make sure nodes get indexed."""
        # A simple TypeDoc JSON dump of a source file with a single, top-level
        # function with no params or return value:
        json = loads(r"""{
          "id": 0,
          "name": "misterRoot",
          "children": [
            {
              "id": 1,
              "name": "\"longnames\"",
              "kindString": "External module",
              "originalName": "/a/b/c/tests/test_typedoc_analysis/source/longnames.ts",
              "children": [
                {
                  "id": 2,
                  "name": "foo",
                  "kindString": "Function",
                  "signatures": [
                    {
                      "id": 3,
                      "name": "foo",
                      "kindString": "Call signature",
                      "comment": {
                        "shortText": "Foo function."
                      },
                      "type": {
                        "type": "intrinsic",
                        "name": "void"
                      }
                    }
                  ],
                  "sources": [
                    {
                      "fileName": "longnames.ts",
                      "line": 4,
                      "character": 12
                    }
                  ]
                }
              ],
              "groups": [
                {
                  "title": "Functions",
                  "children": [
                    2
                  ]
                }
              ],
              "sources": [
                {
                  "fileName": "longnames.ts",
                  "line": 1,
                  "character": 0
                }
              ]
            }
          ],
          "groups": [
            {
              "title": "External modules",
              "children": [
                1
              ]
            }
          ]
        }""")
        index = index_by_id({}, json)
        # Things get indexed by ID:
        function = index[2]
        assert function['name'] == 'foo'
        # Things get parent links:
        assert function['__parent']['name'] == '"longnames"'
        assert function['__parent']['__parent']['name'] == 'misterRoot'
        # Root gets indexed by ID:
        root = index[0]
        assert root['name'] == 'misterRoot'
        # Root parent link is absent or None:
        assert root.get('__parent') is None


class PathSegmentsTests(TypeDocTestCase):
    """Make sure ``make_path_segments() `` works on all its manifold cases."""

    files = ['pathSegments.ts']

    def commented_object(self, comment, **kwargs):
        """Return the object from ``json`` having the given comment short-text."""
        return dict_where(self.json, comment={'shortText': comment}, **kwargs)

    def commented_object_path(self, comment, **kwargs):
        """Return the path segments of the object with the given comment."""
        obj = self.commented_object(comment, **kwargs)
        if obj is NO_MATCH:
            raise RuntimeError(f'No object found with the comment "{comment}".')
        return make_path_segments(obj, self._source_dir)

    def test_class(self):
        assert self.commented_object_path('Foo class') == ['./', 'pathSegments.', 'Foo']

    def test_instance_property(self):
        assert self.commented_object_path('Num instance var') == ['./', 'pathSegments.', 'Foo#', 'numInstanceVar']

    def test_static_property(self):
        assert self.commented_object_path('Static member') == ['./', 'pathSegments.', 'Foo.', 'staticMember']

    def test_interface_property(self):
        assert self.commented_object_path('Interface property') == ['./', 'pathSegments.', 'Face.', 'moof']

    def test_weird_name(self):
        """Make sure property names that themselves contain delimiter chars
        like #./~ get their pathnames built correctly."""
        assert self.commented_object_path('Weird var') == ['./', 'pathSegments.', 'Foo#', 'weird#Var']

    def test_getter(self):
        assert self.commented_object_path('Getter') == ['./', 'pathSegments.', 'Foo#', 'getter']

    def test_setter(self):
        assert self.commented_object_path('Setter') == ['./', 'pathSegments.', 'Foo#', 'setter']

    def test_method(self):
        assert self.commented_object_path('Method') == ['./', 'pathSegments.', 'Foo#', 'someMethod']

    def test_static_method(self):
        """Since ``make_path_segments()`` looks at the inner Call Signature,
        make sure the flags (which determine staticness) are on the node we
        expect."""
        assert self.commented_object_path('Static method') == ['./', 'pathSegments.', 'Foo.', 'staticMethod']

    def test_constructor(self):
        # Pass the kindString so we're sure to find the signature (which is
        # what convert_nodes() passes to make_path_segments()) rather than the
        # constructor itself. They both have the same comments.
        #
        # Constructors get a #. They aren't static; they can see ``this``.
        assert self.commented_object_path('Constructor', kindString='Constructor signature') == ['./', 'pathSegments.', 'Foo#', 'constructor']

    def test_function(self):
        assert self.commented_object_path('Function') == ['./', 'pathSegments.', 'foo']

    def test_relative_paths(self):
        """Make sure FS path segments are emitted if ``base_dir`` doesn't
        directly contain the code."""
        obj = self.commented_object('Function')
        segments = make_path_segments(obj, dirname(dirname(self._source_dir)))
        assert segments == ['./', 'test_typedoc_analysis/', 'source/', 'pathSegments.', 'foo']

    def test_namespaced_var(self):
        """Make sure namespaces get into the path segments."""
        assert self.commented_object_path('Namespaced number') == ['./', 'pathSegments.', 'SomeSpace.', 'spacedNumber']


class ConvertNodeTests(TypeDocAnalyzerTestCase):
    """Test all the branches of ``convert_node()`` by analyzing every kind of
    TypeDoc JSON object."""

    files = ['nodes.ts']

    def test_class(self):
        """Test that superclasses, implemented interfaces, abstractness, and
        nonexistent constructors, members, and top-level attrs are surfaced."""
        # Make sure is_abstract is sometimes false:
        super = self.analyzer.get_object(['Superclass'])
        assert not super.is_abstract

        # There should be a single member representing method():
        method, = super.members
        assert isinstance(method, Function)
        assert method.name == 'method'

        # Class-specific attrs:
        subclass = self.analyzer.get_object(['EmptySubclass'])
        assert isinstance(subclass, Class)
        assert subclass.constructor is None
        assert subclass.is_abstract
        assert subclass.interfaces == [Pathname(['./', 'nodes.', 'Interface'])]

        # _MembersAndSupers attrs:
        assert subclass.supers == [Pathname(['./', 'nodes.', 'Superclass'])]
        assert subclass.members == []

        # TopLevel attrs. This should cover them for other kinds of objs as
        # well (if node structures are the same across object kinds), since we
        # have the filling of them factored out.
        assert subclass.name == 'EmptySubclass'
        assert subclass.path == Pathname(['./', 'nodes.', 'EmptySubclass'])
        assert subclass.filename == 'nodes.ts'
        assert subclass.description == 'An empty subclass'
        assert subclass.deprecated is False
        assert subclass.examples == []
        assert subclass.see_alsos == []
        assert subclass.properties == []
        assert subclass.exported_from == Pathname(['./', 'nodes'])

    def test_interface(self):
        """Test that interfaces get indexed and have their supers exposed.

        Members and top-level properties should be covered in test_class()
        assuming node structure is the same as for classes.

        """
        interface = self.analyzer.get_object(['Interface'])
        assert interface.supers == [Pathname(['./', 'nodes.', 'SuperInterface'])]

    def test_interface_function_member(self):
        """Make sure function-like properties are understood."""
        obj = self.analyzer.get_object(['InterfaceWithMembers'])
        prop = obj.members[0]
        assert isinstance(prop, Function)
        assert prop.name == 'callableProperty'

    def test_variable(self):
        """Make sure top-level consts and vars are found."""
        const = self.analyzer.get_object(['topLevelConst'])
        assert const.type == 'number'

    def test_function(self):
        """Make sure Functions, Params, and Returns are built properly for
        top-level functions.

        This covers a few simple function typing cases as well.

        """
        func = self.analyzer.get_object(['func'])
        assert isinstance(func, Function)
        assert func.params == [
            Param(name='a',
                  description='Some number',
                  has_default=True,
                  is_variadic=False,
                  type='number',
                  default='1'),
            Param(name='b',
                  description='Some strings',
                  has_default=False,
                  is_variadic=True,
                  type='string[]')]
        assert func.exceptions == []
        assert func.returns == [Return(type='number', description='The best number')]

    def test_constructor(self):
        """Make sure constructors get attached to classes and analyzed into
        Functions.

        The rest of their analysis should share a code path with functions.

        """
        cls = self.analyzer.get_object(['ClassWithProperties'])
        assert isinstance(cls.constructor, Function)

    def test_properties(self):
        """Make sure properties are hooked onto classes and expose their
        flags."""
        cls = self.analyzer.get_object(['ClassWithProperties'])
        # The properties are on the class and are Attributes:
        assert len([m for m in cls.members
                    if isinstance(m, Attribute)
                    and m.name in ['someStatic', 'someOptional', 'somePrivate', 'someNormal']]) == 4
        # The unique things about properties (over and above Variables) are set
        # right:
        assert self.analyzer.get_object(['ClassWithProperties.', 'someStatic']).is_static
        assert self.analyzer.get_object(['ClassWithProperties#', 'someOptional']).is_optional
        assert self.analyzer.get_object(['ClassWithProperties#', 'somePrivate']).is_private
        normal_property = self.analyzer.get_object(['ClassWithProperties#', 'someNormal'])
        assert (not normal_property.is_optional and
                not normal_property.is_static and
                not normal_property.is_abstract and
                not normal_property.is_private)

    def test_getter(self):
        """Test that we represent getters as Attributes and find their return
        types."""
        getter = self.analyzer.get_object(['gettable'])
        assert isinstance(getter, Attribute)
        assert getter.type == 'number'

    def test_setter(self):
        """Test that we represent setters as Attributes and find the type of
        their 1 param."""
        setter = self.analyzer.get_object(['settable'])
        assert isinstance(setter, Attribute)
        assert setter.type == 'string'


class TypeNameTests(TypeDocAnalyzerTestCase):
    """Make sure our rendering of TypeScript types into text works."""

    files = ['types.ts']

    def test_basic(self):
        """Test intrinsic types."""
        for obj_name, type_name in [
                ('bool', 'boolean'),
                ('num', 'number'),
                ('str', 'string'),
                ('array', 'number[]'),
                ('genericArray', 'Array<number>'),
                ('tuple', '[string, number]'),
                ('color', 'Color'),
                ('unk', 'unknown'),
                ('whatever', 'any'),
                ('voidy', 'void'),
                ('undef', 'undefined'),
                ('nully', 'null'),
                ('nev', 'never'),
                ('obj', 'object'),
                ('sym', 'symbol')]:
            obj = self.analyzer.get_object([obj_name])
            assert obj.type == type_name

    def test_named_interface(self):
        """Make sure interfaces can be referenced by name."""
        obj = self.analyzer.get_object(['interfacer'])
        assert obj.params[0].type == 'Interface'

    def test_interface_readonly_member(self):
        """Make sure the readonly modifier doesn't keep us from computing the
        type of a property."""
        obj = self.analyzer.get_object(['Interface'])
        read_only_num = obj.members[0]
        assert read_only_num.name == 'readOnlyNum'
        assert read_only_num.type == 'number'

    def test_array(self):
        """Make sure array types are rendered correctly.

        As a bonus, make sure we grab the first signature of an overloaded
        function.

        """
        obj = self.analyzer.get_object(['overload'])
        assert obj.params[0].type == 'string[]'

    def test_literal_types(self):
        """Make sure a thing of a named literal type has that type name
        attached."""
        obj = self.analyzer.get_object(['certainNumbers'])
        assert obj.type == 'CertainNumbers'

    def test_unions(self):
        """Make sure unions get rendered properly."""
        obj = self.analyzer.get_object(['union'])
        assert obj.type == 'number|string|Color'

    def test_intersection(self):
        obj = self.analyzer.get_object(['intersection'])
        assert obj.type == 'FooHaver & BarHaver'

    def test_generic_function(self):
        """Make sure type params appear in args and return types."""
        obj = self.analyzer.get_object(['aryIdentity'])
        assert obj.params[0].type == 'T[]'
        assert obj.returns[0].type == 'T[]'

    @pytest.mark.xfail(reason='reflection not implemented yet')
    def test_generic_member(self):
        """Make sure members of a class have their type params taken into
        account."""
        obj = self.analyzer.get_object(['add'])
        assert obj.type == 'T'
        assert obj.params[0].type == 'T'

    def test_constrained_by_interface(self):
        """Make sure ``extends SomeInterface`` constraints are rendered."""
        obj = self.analyzer.get_object(['constrainedIdentity'])
        assert obj.params[0].type == 'T extends Lengthwise'
        assert obj.returns[0].type == 'T extends Lengthwise'

    def test_constrained_by_key(self):
        """Make sure ``extends keyof SomeObject`` constraints are rendered."""
        obj = self.analyzer.get_object(['getProperty'])
        assert obj.params[1].type == 'K extends keyof T'

    @pytest.mark.xfail(reason='reflection not implemented yet')
    def test_constrained_by_constructor(self):
        """Make sure ``new ()`` expressions and, more generally, per-property
        constraints are rendered properly."""
        obj = self.analyzer.get_object(['create'])
        assert obj.params[0].type == '{new (): T}'

    def test_utility_types(self):
        """Test that a representative one of TS's utility types renders."""
        obj = self.analyzer.get_object(['partial'])
        assert obj.type == 'Partial<string>'

    @pytest.mark.xfail(reason='reflection not implemented yet')
    def test_constrained_by_property(self):
        obj = self.analyzer.get_object(['objProps'])
        assert obj.params[0].type == '{label: string}'

    @pytest.mark.xfail(reason='reflection not implemented yet')
    def test_optional_property(self):
        """Make sure optional properties render properly."""
        obj = self.analyzer.get_object(['option'])
        assert obj.type == '{a: number; b?: string}'
