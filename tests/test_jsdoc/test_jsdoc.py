from os.path import dirname, join

from sphinx_js.ir import Attribute, Class, Exc, Function, Param, Return
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
        """Test Class analysis."""
        cls = self.analyzer.get_object(['Foo'], 'class')
        assert cls.name == 'Foo'
        assert cls.path_segments == ['./', 'class.', 'Foo']
        assert cls.filename == 'class.js'
        assert cls.description == 'Class doc.'
        assert cls.line == 14  # Not ideal, as it refers to the constructor, but we'll allow it
        assert cls.examples == ['Example in constructor']  # We ignore examples and other fields from the class doclet so far. This could change someday.

        # Members:
        getter, private_method = cls.members  # default constructor not included here
        assert isinstance(private_method, Function)
        assert private_method.name == 'secret'
        assert private_method.path_segments == ['./', 'class.', 'Foo#', 'secret']
        assert private_method.description == 'Private method.'
        assert private_method.is_private == True
        assert isinstance(getter, Attribute)
        assert getter.name == 'bar'
        assert getter.path_segments == ['./', 'class.', 'Foo#', 'bar']
        assert getter.filename == 'class.js'
        assert getter.description == 'Setting this also frobs the frobnicator.'

        # Constructor:
        constructor = cls.constructor
        assert constructor.name == 'Foo'
        assert constructor.path_segments == ['./', 'class.', 'Foo']  # Same path as class. This might differ in different languages.
        assert constructor.filename == 'class.js'
        assert constructor.description == 'Constructor doc.'
        assert constructor.examples == ['Example in constructor']
        assert constructor.params == [Param(name='ho',
                                            description='A thing',
                                            has_default=False,
                                            is_variadic=False,
                                            types=[])]
        assert constructor.exceptions == [
            Exc(types=[],
                description='ExplosionError It went boom.')]

# NEXT: Test exceptions and returns, unless the RST tests are good enough for that.
