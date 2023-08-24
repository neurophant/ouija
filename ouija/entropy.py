from random import randrange

import numpy as np


class Entropy:
    @staticmethod
    def calculate(*, data: bytes) -> float:
        array = np.frombuffer(data, dtype='S1')
        _, counts = np.unique(array, return_counts=True)
        probs = counts / array.size
        return -np.sum(probs * np.log2(probs))

    def decrease(self, *, data: bytes) -> bytes:
        raise NotImplementedError

    def increase(self, *, data: bytes) -> bytes:
        raise NotImplementedError


class SpaceEntropy(Entropy):
    every: int

    def __init__(self, *, every: int):
        self.every = every

    def decrease(self, *, data: bytes) -> bytes:
        decreased = b''
        for idx in range(0, len(data), self.every - 1):
            decreased += bytes(data[idx:idx + self.every - 1]) + bytes(data[randrange(0, len(data))])
        return decreased

    def increase(self, *, data: bytes) -> bytes:
        increased = b''
        for idx in range(0, len(data), self.every):
            increased += bytes(data[idx:idx + self.every - 1])
        return increased
