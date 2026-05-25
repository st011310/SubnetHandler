from dataclasses import dataclass

@dataclass
class Gate:
    id: int
    op: str
    input0: int
    input1: int


@dataclass
class Circuit:
    n: int
    gates: list[Gate]
    output_gate: int

