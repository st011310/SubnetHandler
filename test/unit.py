from src.utils import infer_n_from_truth_vector
from src import find_circuit, print_circuit, circuit_truth_vector, visualize_circuit

def unitTest(truth_vector: str | list[int] | tuple[int,...], dirpath: str):
    n = 2 * infer_n_from_truth_vector(truth_vector) # сложность -- удвоенное число входов

    tt_str = "".join(map(str,truth_vector))
    _, _, circuit = find_circuit(
        N=n,
        truth_vector=truth_vector,
        output_mode="any",
        dimacs_path=f"{dirpath}{tt_str}.cnf",
        solver="z3"
    )
    if circuit is not None:
        dot = visualize_circuit(circuit, filename=f"{dirpath}{tt_str}")
        dot


