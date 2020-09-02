import pytest

from sphinx_js.ir import Param


def test_default():
    """Accessing ``.default`` on a Param having a default should return the
    default value."""
    p = Param(name='fred',
              has_default=True,
              default='boof')
    assert p.default == 'boof'


def test_missing_default():
    """Constructing a Param with ``has_default=True`` but without a ``default``
    value should raise an error."""
    with pytest.raises(ValueError):
        Param(name='fred',
              has_default=True)
