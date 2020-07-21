from os.path import dirname, join

from sphinx_js.ir import Class, Exc, Function, Param, Return
from tests.testing import JsDocTestCase


class FunctionTests(JsDocTestCase):
    file = 'function.js'

    def test_top_level_and_function(self):
        """Smoke-test Function (and thus also TopLevel) analysis."""
        function = self.analyzer.get_object(['foo'], 'function')
        assert function == Function(
            name='foo',
            path_segments=['./', 'function.', 'foo'],
            filename='function.js',
            description='Function foo.',
            line=9,
            deprecated=False,
            examples=[],
            see_alsos=[],
            properties=[],
            is_private=False,
            params=[Param(name='bar',
                          description='Which bar',
                          has_default=False,
                          is_variadic=False,
                          types=['String']),
                    Param(name='baz',
                          description='',
                          has_default=True,
                          default='8',
                          is_variadic=False,
                          types=[])],
            exceptions=[],
            returns=[
                Return(types=['Number'],
                       description='How many things there are')])  # Test text unwrapping.


class ClassTests(JsDocTestCase):
    file = 'class.js'

    def test_class(self):
        """Smoke-test Class analysis."""
        cls = self.analyzer.get_object(['Foo'], 'class')
        assert cls == Class(name='Foo',
                            path_segments=['./', 'class.', 'Foo'],
                            filename='class.js',
                            description='Class doc.',
                            line=14,  # Not ideal, as it refers to the constructor, but we'll allow it
                            deprecated=False,
                            examples=['Example in constructor'],
                            see_alsos=[],
                            properties=[],
                            is_private=False,
                            members=[],
                            constructor=Function(
                                name='Foo',
                                path_segments=['./', 'class.', 'Foo'],
                                filename='class.js',
                                description='Constructor doc.',
                                line=14,
                                deprecated=False,
                                examples=['Example in constructor'],
                                see_alsos=[],
                                properties=[],
                                is_private=False,
                                params=[Param(
                                    name='ho',
                                    description='A thing',
                                    has_default=False,
                                    is_variadic=False,
                                    types=[])],
                                exceptions=[Exc(types=[],
                                                description='ExplosionError It went boom.')],
                                returns=[]))
# NEXT: Get rid of the uninformative fields ^^^ here. Give them defaults in the IR.

# NEXT: Test exceptions and returns, unless the RST tests are good enough for that.
# Test Class.
