from graphviz import Digraph

from .data import Circuit

def visualize_circuit(circuit: Circuit, filename: str = "circuit", view: bool = False):
    """
    Построить граф схемы через Graphviz.
    """
    dot = Digraph("Circuit")
    dot.attr(rankdir="LR")

    for i in range(circuit.n):
        dot.node(f"x{i}", f"x{i}", shape="box")

    for gate in circuit.gates:
        attrs = {"shape": "circle"}
        if gate.id == circuit.output_gate:
            attrs = {"shape": "doublecircle"}
        dot.node(f"g{gate.id}", f"g{gate.id}\n{gate.op}", **attrs)

        def src_node(s):
            return f"x{s}" if s < circuit.n else f"g{s - circuit.n}"

        dot.edge(src_node(gate.input0), f"g{gate.id}", label="1")
        dot.edge(src_node(gate.input1), f"g{gate.id}", label="2")

    dot.node("out", "OUT", shape="plaintext")
    dot.edge(f"g{circuit.output_gate}", "out")

    try:
        dot.render(filename, format="png", cleanup=True, view=view)
    except Exception as e:
        print("Graphviz-объект создан, но PNG не сохранён. Возможная причина: не установлен системный graphviz.")
        print(e)

    return dot

