import itertools
import math


def assignments(n: int) -> list[tuple[int, ...]]:
    """Все наборы входов в порядке, соответствующем truth_vector."""
    return list(itertools.product([0, 1], repeat=n))

def infer_n_from_truth_vector(truth_vector: str | list[int] | tuple[int, ...]) -> int:
    """Определить число переменных по длине вектора значений."""
    m = len(truth_vector)
    n = int(math.log2(m))
    assert 2 ** n == m, "Длина truth_vector должна быть степенью двойки: 2^n"
    return n

def normalize_truth_vector(truth_vector: str | list[int] | tuple[int, ...]) -> tuple[int, ...]:
    tv = tuple(int(x) for x in truth_vector)
    assert any(x in (0, 1) for x in tv), "truth_vector должен состоять только из 0 и 1"
    return tv

def truth_vector_from_function(n: int, func) -> tuple[int, ...]:
    """Построить truth_vector для Python-функции func(x0, ..., x_{n-1})."""
    return tuple(int(bool(func(*alpha))) for alpha in assignments(n))

