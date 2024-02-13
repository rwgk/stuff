import pickle

import pytest

from build import test_pickle_simple_callable as m


def test_assumptions():
    assert pickle.HIGHEST_PROTOCOL >= 0


@pytest.mark.parametrize("protocol", range(pickle.HIGHEST_PROTOCOL + 1))
def test_pickle_simple_callable(protocol):
    assert m.simple_callable() == 723
    serialized = pickle.dumps(m.simple_callable, protocol=protocol)
    assert b"test_pickle_simple_callable" in serialized
    assert b"simple_callable" in serialized
    deserialized = pickle.loads(serialized)
    assert deserialized() == 723

