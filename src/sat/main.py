import subprocess
import os

from src.cnf.builder import CNFBuilder

def solve_cnf_with_z3(cnf: CNFBuilder, timeout_ms: int | None = None):
    """
    Решить CNF через z3-solver.

    Установка при необходимости:
        pip install z3-solver
    """
    try:
        import z3
    except ImportError as e:
        raise ImportError("Не установлен z3-solver. Выполните: pip install z3-solver") from e

    zvars = {i: z3.Bool(f"v{i}") for i in range(1, cnf.num_vars + 1)}
    solver = z3.Solver()
    if timeout_ms is not None:
        solver.set(timeout=timeout_ms)

    for clause in cnf.clauses:
        solver.add(z3.Or([zvars[abs(lit)] if lit > 0 else z3.Not(zvars[abs(lit)]) for lit in clause]))

    result = solver.check()
    if result == z3.sat:
        model_z3 = solver.model()
        model = {}
        for i in range(1, cnf.num_vars + 1):
            val = model_z3.eval(zvars[i], model_completion=True)
            model[i] = bool(z3.is_true(val))
        return "SAT", model
    if result == z3.unsat:
        return "UNSAT", None
    return "UNKNOWN", None

def solve_dimacs_with_external_solver(
    dimacs_path: str,
    solver_cmd: str = "minisat",
    result_path: str = "sat_result.out",
):
    """
    Запустить внешний SAT-solver по DIMACS-файлу.

    Пример:
        status, model = solve_dimacs_with_external_solver('circuit.cnf', 'minisat')

    Подходит для MiniSat. Для CaDiCaL/Kissat формат вывода может немного отличаться.
    """
    completed = subprocess.run(
        [solver_cmd, dimacs_path, result_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    if not os.path.exists(result_path):
        raise RuntimeError(
            f"Solver не создал файл результата. stdout:\n{completed.stdout}\nstderr:\n{completed.stderr}"
        )

    with open(result_path, "r", encoding="utf-8", errors="ignore") as f:
        data = f.read().strip().split()

    if not data:
        return "UNKNOWN", None

    status = data[0].upper()
    if status == "SAT":
        model = {}
        for token in data[1:]:
            lit = int(token)
            if lit == 0:
                break
            model[abs(lit)] = lit > 0
        return "SAT", model
    if status == "UNSAT":
        return "UNSAT", None
    return "UNKNOWN", None

def solve_cnf_small_dpll(cnf: CNFBuilder, max_vars_for_demo: int = 80):
    """
    Очень простой встроенный DPLL для маленьких примеров.
    Нужен только как fallback, чтобы ноутбук запускался без внешних пакетов.
    Для реального задания лучше использовать z3/minisat/cadical/kissat.
    """
    if cnf.num_vars > max_vars_for_demo:
        return "UNKNOWN", None

    clauses = [list(c) for c in cnf.clauses]

    def simplify(clauses, assignment):
        new_clauses = []
        changed = True
        while changed:
            changed = False
            units = []
            for clause in clauses:
                satisfied = False
                unassigned = []
                for lit in clause:
                    var = abs(lit)
                    if var in assignment:
                        if assignment[var] == (lit > 0):
                            satisfied = True
                            break
                    else:
                        unassigned.append(lit)
                if satisfied:
                    continue
                if not unassigned:
                    return None, assignment
                if len(unassigned) == 1:
                    units.append(unassigned[0])
                new_clauses.append(unassigned)

            for lit in units:
                var = abs(lit)
                val = lit > 0
                if var in assignment and assignment[var] != val:
                    return None, assignment
                if var not in assignment:
                    assignment[var] = val
                    changed = True

            if changed:
                clauses = new_clauses
                new_clauses = []

        return new_clauses, assignment

    def dpll(clauses, assignment):
        clauses, assignment = simplify(clauses, dict(assignment))
        if clauses is None:
            return None
        if not clauses:
            return assignment

        # Выбираем переменную из самой короткой клаузы.
        lit = min(clauses, key=len)[0]
        var = abs(lit)
        for val in [True, False]:
            new_assignment = dict(assignment)
            new_assignment[var] = val
            result = dpll(clauses, new_assignment)
            if result is not None:
                return result
        return None

    model = dpll(clauses, {})
    if model is None:
        return "UNSAT", None
    for var_id in range(1, cnf.num_vars + 1):
        model.setdefault(var_id, False)
    return "SAT", model

def solve_cnf(cnf: CNFBuilder, prefer: str = "z3", timeout_ms: int | None = None):
    """
    Удобная обёртка.
    prefer='z3' — основной вариант.
    Если z3 не установлен и формула маленькая, пробует встроенный DPLL.
    """
    if prefer == "z3":
        try:
            return solve_cnf_with_z3(cnf, timeout_ms=timeout_ms)
        except ImportError:
            return solve_cnf_small_dpll(cnf)
    if prefer == "dpll":
        return solve_cnf_small_dpll(cnf)
    raise ValueError("prefer должен быть 'z3' или 'dpll'")


