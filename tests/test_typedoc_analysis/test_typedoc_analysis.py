from json import loads
from os.path import dirname
from unittest import TestCase

from sphinx_js.ir import Attribute, Class, Exc, Function, Param, Return
from sphinx_js.typedoc import index_by_id, make_path_segments

from tests.testing import dict_where, NO_MATCH, TypeDocAnalyzerTestCase, TypeDocTestCase


class IndexByIdTests(TestCase):
    def test_top_level_function(self):
        """Make sure nodes get indexed"""
        # A simple TypeDoc JSON dump of a soruce file with a single, top-level
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


class AnalyzerTests(TypeDocAnalyzerTestCase):
    files = ['analysis.ts']

    def test_class(self):
        """Test that superclasses, implemented interfaces, abstractness, and
        nonexistent constructors are surfaced."""
        # Make sure is_abstract is sometimes false:
        super = self.analyzer.get_object(['Superclass'])
        assert not super.is_abstract

        # Class-specific attrs:
        subclass = self.analyzer.get_object(['EmptySubclass'])
        assert isinstance(subclass, Class)
        assert subclass.constructor is None
        assert subclass.is_abstract
        assert subclass.interfaces == ['analysis.Interface']

        # _MembersAndSupers attrs:
        assert subclass.supers == ['analysis.Superclass']
