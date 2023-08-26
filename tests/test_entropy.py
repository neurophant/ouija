import pytest

from ouija import Entropy


@pytest.mark.xfail(raises=NotImplementedError)
def test_entropy_decrease(data_test):
    entropy = Entropy()
    entropy.decrease(data=data_test)


@pytest.mark.xfail(raises=NotImplementedError)
def test_entropy_increase(data_test):
    entropy = Entropy()
    entropy.increase(data=data_test)


def test_simple_entropy(entropy_test, data_test):
    decreased = entropy_test.decrease(data=data_test)
    increased = entropy_test.increase(data=decreased)

    assert increased == data_test
