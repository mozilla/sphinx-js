from json import loads

from sphinx_js.ir import Attribute, Class, Exc, Function, Param, Return
from sphinx_js.typedoc import index_by_id, make_longname
from tests.testing import TypeDocTestCase


class ThisDirTestCase(TypeDocTestCase):
    files = ['longnames.ts']

    def test_top_level_function(self):
        json = loads(r"""{
          "id": 0,
          "name": "misterRoot",
          "kind": 0,
          "flags": {},
          "children": [
            {
              "id": 1,
              "name": "\"longnames\"",
              "kind": 1,
              "kindString": "External module",
              "flags": {
                "isExported": true
              },
              "originalName": "/a/b/c/tests/test_typedoc_analysis/source/longnames.ts",
              "children": [
                {
                  "id": 2,
                  "name": "foo",
                  "kind": 64,
                  "kindString": "Function",
                  "flags": {},
                  "signatures": [
                    {
                      "id": 3,
                      "name": "foo",
                      "kind": 4096,
                      "kindString": "Call signature",
                      "flags": {},
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
                  "kind": 64,
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
              "kind": 1,
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
        # Things get indexed by ID:
        root = index[0]
        assert root['name'] == 'misterRoot'
        # Root parent link is absent or None:
        assert root.get('__parent') is None
        #assert make_longname(json) self.analyzer


# class TypeDocAnalyzerTestCase:
#     def test_class(self):
#         cls = self.analyzer.get_object(['ClassDefinition'])
#         assert isinstance(cls, Class)
#         assert the members are right
