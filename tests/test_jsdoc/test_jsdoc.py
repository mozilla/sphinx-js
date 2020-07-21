from os.path import dirname, join

from sphinx_js.ir import Class, Function, Param, Return
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
