import numpy as np


def calculate(*, data: bytes) -> float:
    array = np.frombuffer(data, dtype='S1')
    _, counts = np.unique(array, return_counts=True)
    probs = counts / array.size
    return -np.sum(probs * np.log2(probs))


def relieve(*, data: bytes) -> bytes:
    pass


def aggravate(*, data: bytes) -> bytes:
    pass
