from .data import Gate, Circuit
from src.cnf.encoding import CircuitEncoding

def extract_circuit(enc: CircuitEncoding, model: dict[int, bool]) -> Circuit:
    """Восстановить схему из SAT-модели."""
    gates = []

    for g in range(enc.N):
        op_id = next(
            op_id for op_id in range(len(enc.basis))
            if model.get(enc.op_var[(g, op_id)], False)
        )
        op_name = enc.basis[op_id][0]

        sources = list(range(enc.n + g))
        input0 = next(
            s for s in sources
            if model.get(enc.input_var[(g, 0, s)], False)
        )
        input1 = next(
            s for s in sources
            if model.get(enc.input_var[(g, 1, s)], False)
        )

        gates.append(Gate(id=g, op=op_name, input0=input0, input1=input1))

    if enc.output_mode == "last":
        output_gate = enc.N - 1
    else:
        output_gate = next(g for g in range(enc.N) if model.get(enc.output_var[g], False))

    return Circuit(n=enc.n, gates=gates, output_gate=output_gate)

