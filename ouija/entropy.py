import numpy as np


class Entropy:
    """Base class for entropy implementation"""

    @staticmethod
    def calculate(*, data: bytes) -> float:
        array = np.frombuffer(data, dtype='B')
        _, counts = np.unique(array, return_counts=True)
        probs = counts / array.size
        return -np.sum(probs * np.log2(probs))

    def decrease(self, *, data: bytes) -> bytes:
        raise NotImplementedError

    def increase(self, *, data: bytes) -> bytes:
        raise NotImplementedError


class SimpleEntropy(Entropy):
    """Simple entropy"""

    rate: int

    def __init__(self, *, rate: int) -> None:
        self.rate = rate

    def decrease(self, *, data: bytes) -> bytes:
        array = np.frombuffer(data, dtype='B')
        values, counts = np.unique(array, return_counts=True)
        array_dict = {counts[idx]: values[idx:idx + 1] for idx in range(len(values))}
        filler = array_dict[max(array_dict)].tobytes()

        decreased = b''
        for idx in range(0, len(data), self.rate - 1):
            decreased += data[idx:idx + self.rate - 1]
            if len(data) - idx >= self.rate - 1:
                decreased += filler

        return decreased

    def increase(self, *, data: bytes) -> bytes:
        increased = b''

        for idx in range(0, len(data), self.rate):
            increased += data[idx:idx + self.rate - 1]

        return increased
