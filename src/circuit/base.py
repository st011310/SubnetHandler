from .data import Circuit
from src.utils import normalize_truth_vector, assignments
from src.consts import BASIS
from src.cnf.encoding import build_circuit_cnf
from src.sat.main import solve_cnf
from .sat import extract_circuit

def _source_value_for_circuit(circuit: Circuit, values: list[bool], alpha: tuple[int, ...], source: int) -> bool:
    if source < circuit.n:
        return bool(alpha[source])
    return values[source - circuit.n]


def evaluate_circuit(circuit: Circuit, alpha: tuple[int, ...]) -> bool:
    values = []
    for gate in circuit.gates:
        a = _source_value_for_circuit(circuit, values, alpha, gate.input0)
        b = _source_value_for_circuit(circuit, values, alpha, gate.input1)

        for name, ar, f in BASIS:
            if gate.op == name:
                values.append(f(a, b))
                break
        else:
            raise ValueError(f"Неизвестная операция: {gate.op}")

    return values[circuit.output_gate]

def circuit_truth_vector(circuit: Circuit) -> tuple[int, ...]:
    return tuple(int(evaluate_circuit(circuit, alpha)) for alpha in assignments(circuit.n))


def check_circuit(circuit: Circuit, truth_vector: str | list[int] | tuple[int, ...]) -> bool:
    return circuit_truth_vector(circuit) == normalize_truth_vector(truth_vector)


def print_circuit(circuit: Circuit):
    """Текстовое описание схемы."""
    for i in range(circuit.n):
        print(f"x{i}: input")
    for gate in circuit.gates:
        def src_name(s):
            return f"x{s}" if s < circuit.n else f"g{s - circuit.n}"
        marker = "  <-- OUTPUT" if gate.id == circuit.output_gate else ""
        print(f"g{gate.id}: {gate.op}({src_name(gate.input0)}, {src_name(gate.input1)}){marker}")

def find_circuit(
    N: int,
    truth_vector: str | list[int] | tuple[int, ...],
    output_mode: str = "any",
    dimacs_path: str = "circuit.cnf",
    solver: str = "z3",
    timeout_ms: int | None = None,
):
    """
    Полный pipeline:
    1. строит CNF;
    2. сохраняет DIMACS;
    3. запускает SAT-решатель;
    4. восстанавливает схему при SAT.
    """
    enc = build_circuit_cnf(
        N=N,
        truth_vector=truth_vector,
        basis=BASIS,
        output_mode=output_mode,
        allow_same_input=True,
    )

    enc.cnf.write_dimacs(dimacs_path)
    print(f"CNF сохранена в {dimacs_path}")
    print(f"Переменных: {enc.cnf.num_vars}")
    print(f"Клауз: {len(enc.cnf.clauses)}")

    status, model = solve_cnf(enc.cnf, prefer=solver, timeout_ms=timeout_ms)
    print(f"SAT solver result: {status}")

    if status != "SAT":
        return enc, status, None

    assert model is not None
    circuit = extract_circuit(enc, model)
    ok = check_circuit(circuit, truth_vector)
    print(f"Проверка найденной схемы по truth_vector: {'OK' if ok else 'FAIL'}")

    return enc, status, circuit

def find_minimal_circuit(
    truth_vector: str | list[int] | tuple[int, ...],
    max_N: int,
    solver: str = "z3",
    timeout_ms: int | None = None,
):
    """Последовательно ищет минимальную схему размера <= max_N."""
    for N in range(1, max_N + 1):
        print("=" * 70)
        print(f"Пробуем N = {N}")
        enc, status, circuit = find_circuit(
            N=N,
            truth_vector=truth_vector,
            output_mode="any",
            dimacs_path=f"circuit_N{N}.cnf",
            solver=solver,
            timeout_ms=timeout_ms,
        )
        if status == "SAT":
            print(f"Минимальная найденная сложность: <= {N}")
            return N, enc, circuit
        if status == "UNKNOWN":
            print("Solver вернул UNKNOWN. Дальше минимальность строго доказать нельзя.")
            return None, enc, None
    print(f"Схема размера <= {max_N} не найдена.")
    return None, None, None
