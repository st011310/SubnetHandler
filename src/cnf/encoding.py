from dataclasses import dataclass
from typing import Callable

from src.cnf.builder import CNFBuilder
from src.utils import assignments, normalize_truth_vector, infer_n_from_truth_vector
from src.consts import BASIS

@dataclass
class CircuitEncoding:
    n: int
    N: int
    truth_vector: tuple[int, ...]
    basis: list[tuple[str, int, Callable]]
    cnf: CNFBuilder
    input_var: dict[tuple[int, int, int], int]     # (gate, port, source) -> var
    op_var: dict[tuple[int, int], int]             # (gate, op_id) -> var
    value_var: dict[tuple[int, int], int]          # (gate, assignment_id) -> var
    output_var: dict[int, int]                     # gate -> var, if output_mode == 'any'
    output_mode: str


def _source_eq_literal(enc: CircuitEncoding, source: int, assignment_id: int, bit: int) -> int | bool:
    """
    Литерал, означающий: значение источника source на наборе assignment_id равно bit.
    Возвращает:
    - True/False, если источник — исходная переменная и значение известно константно;
    - литерал int, если источник — выход предыдущего гейта.
    """
    alpha = assignments(enc.n)[assignment_id]

    if source < enc.n:
        return bool(alpha[source] == bit)

    gate_id = source - enc.n
    v = enc.value_var[(gate_id, assignment_id)]
    return v if bit == 1 else -v

def _negate_condition_literal(lit: int | bool) -> int | None:
    """
    Для импликации cond -> out в CNF нужна отрицательная форма условия.
    Если cond константно True — ничего не добавляем.
    Если cond константно False — вся импликация тривиальна, её можно пропустить.
    """
    if lit is True:
        return None
    if lit is False:
        return False
    return -lit

def _negate_and_literal(lit: int | bool) -> int | None:
    """
    Для импликации cond -> out в CNF нужна отрицательная форма условия.
    Если cond константно True — ничего не добавляем.
    Если cond константно False — вся импликация тривиальна, её можно пропустить.
    """
    if lit is True:
        return None
    if lit is False:
        return False
    return -lit

def build_circuit_cnf(
    N: int,
    truth_vector: str | list[int] | tuple[int, ...],
    basis: list[tuple[str, int, Callable]] = BASIS,
    output_mode: str = "any",
    allow_same_input: bool = True,
) -> CircuitEncoding:
    """
    Построить CNF для существования схемы в заданном базисе.

    output_mode:
    - 'any': выходом может быть любой из N гейтов. Тогда проверяется существование схемы размера <= N.
    - 'last': выходом считается последний гейт. Это ближе к формулировке "ровно N гейтов".

    allow_same_input:
    - True: один и тот же источник можно подать на оба входа гейта.
      Для базиса {IMP, XOR} это важно, потому что x -> x = 1, x XOR x = 0.
    - False: запрещает одинаковые источники на двух входах одного гейта.
    """
    assert all(arity <= 2 for _, arity, _ in BASIS)

    if output_mode not in {"any", "last"}:
        raise ValueError("output_mode должен быть 'any' или 'last'")
    if N <= 0:
        raise ValueError("В этой реализации N должен быть >= 1")

    tv = normalize_truth_vector(truth_vector)
    n = infer_n_from_truth_vector(tv)
    alphas = assignments(n)

    cnf = CNFBuilder()
    input_var = {}
    op_var = {}
    value_var = {}
    output_var = {}

    # 1. Переменные выбора операции каждого гейта.
    for g in range(N):
        op_choices = []
        for op_id, (op_name, *_) in enumerate(basis):
            v = cnf.new_var(f"op_g{g}_{op_name}")
            op_var[(g, op_id)] = v
            op_choices.append(v)
        cnf.exactly_one(op_choices)

    # 2. Переменные выбора входов каждого гейта.
    # Источники для g: исходные x0..x(n-1) и предыдущие гейты g0..g(g-1).
    for g in range(N):
        sources = list(range(n + g))
        for port in [0, 1]:
            choices = []
            for source in sources:
                v = cnf.new_var(f"in_g{g}_p{port}_s{source}")
                input_var[(g, port, source)] = v
                choices.append(v)
            cnf.exactly_one(choices)

        if not allow_same_input:
            for source in sources:
                cnf.add_clause([
                    -input_var[(g, 0, source)],
                    -input_var[(g, 1, source)],
                ])

    # 3. Переменные значений гейтов на каждом входном наборе.
    for g in range(N):
        for assignment_id, _alpha in enumerate(alphas):
            value_var[(g, assignment_id)] = cnf.new_var(f"val_g{g}_a{assignment_id}")

    enc = CircuitEncoding(
        n=n,
        N=N,
        truth_vector=tv,
        basis=basis,
        cnf=cnf,
        input_var=input_var,
        op_var=op_var,
        value_var=value_var,
        output_var=output_var,
        output_mode=output_mode,
    )

    # 4. Семантика каждого гейта на каждом наборе входов.
    # Если выбран op, выбран source0, выбран source1, а их значения b0/b1,
    # то val_g_a должен равняться op(b0, b1).
    for g in range(N):
        sources = list(range(n + g))
        for assignment_id, _alpha in enumerate(alphas):
            out_var = value_var[(g, assignment_id)]

            for op_id, (_op_name, ar, op_func) in enumerate(basis):
                op_choice = op_var[(g, op_id)]

                for s0 in sources:
                    c0 = input_var[(g, 0, s0)]
                    for s1 in sources:
                        c1 = input_var[(g, 1, s1)]

                        for b0 in [0, 1]:
                            lit0 = _source_eq_literal(enc, s0, assignment_id, b0)
                            neg_lit0 = _negate_condition_literal(lit0)
                            if neg_lit0 is False:
                                continue

                            for b1 in [0, 1]:
                                lit1 = _source_eq_literal(enc, s1, assignment_id, b1)
                                neg_lit1 = _negate_condition_literal(lit1)
                                if neg_lit1 is False:
                                    continue

                                out_bit = int(bool(op_func(bool(b0), bool(b1))))
                                out_lit = out_var if out_bit == 1 else -out_var

                                clause = [-op_choice, -c0, -c1]
                                if neg_lit0 is not None:
                                    clause.append(neg_lit0)
                                if neg_lit1 is not None:
                                    clause.append(neg_lit1)
                                clause.append(out_lit)
                                cnf.add_clause(clause)

    # 5. Ограничение на выход схемы.
    if output_mode == "last":
        output_gate = N - 1
        for assignment_id, target in enumerate(tv):
            v = value_var[(output_gate, assignment_id)]
            cnf.add_unit(v if target == 1 else -v)
    else:
        # Выходом может быть любой гейт. Это даёт проверку "сложность <= N".
        out_choices = []
        for g in range(N):
            v = cnf.new_var(f"output_is_g{g}")
            output_var[g] = v
            out_choices.append(v)
        cnf.exactly_one(out_choices)

        for g in range(N):
            out_choice = output_var[g]
            for assignment_id, target in enumerate(tv):
                val = value_var[(g, assignment_id)]
                cnf.add_clause([-out_choice, val if target == 1 else -val])

    return enc

