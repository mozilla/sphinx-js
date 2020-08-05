from json import loads
from unittest import TestCase

from sphinx_js.ir import Attribute, Class, Exc, Function, Param, Return
from sphinx_js.typedoc import index_by_id, make_path_segments

from tests.testing import dict_where, TypeDocTestCase


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
        index = {}
        index_by_id(index, json)
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



class LongNameTests(TypeDocTestCase):
    files = ['longnames.ts']

    def commented_object(self, comment):
        """Return the object from ``json`` having the given comment short-text."""
        return dict_where(self.json, comment={'shortText': comment})

    def commented_object_path(self, comment):
        """Return the path segments of the object with the given comment."""
        obj = self.commented_object(comment)
        return make_path_segments(obj, self._source_dir)

    def test_top_level(self):
        assert self.commented_object_path('Foo class') == ['longnames.', 'Foo']

    def test_instance_property(self):
        assert self.commented_object_path('Num instance var') == ['longnames.', 'Foo#', 'numInstanceVar']

    def test_static_property(self):
        assert self.commented_object_path('Static member') == ['longnames.', 'Foo.', 'staticMember']
        #assert make_longname(json) self.analyzer


# class TypeDocAnalyzerTestCase:
#     def test_class(self):
#         cls = self.analyzer.get_object(['ClassDefinition'])
#         assert isinstance(cls, Class)
#         assert the members are right
