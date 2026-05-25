import itertools
from dataclasses import dataclass, field


@dataclass
class CNFBuilder:
    clauses: list[list[int]] = field(default_factory=list)
    names: dict[int, str] = field(default_factory=dict)
    ids: dict[str, int] = field(default_factory=dict)
    _next_var: int = 1

    def new_var(self, name: str) -> int:
        if name in self.ids:
            return self.ids[name]
        v = self._next_var
        self._next_var += 1
        self.ids[name] = v
        self.names[v] = name
        return v

    @property
    def num_vars(self) -> int:
        return self._next_var - 1

    def add_clause(self, clause: list[int]):
        # Удаляем дубли литералов. Если есть x и -x, клауза тавтологична.
        s = set(clause)
        for lit in list(s):
            if -lit in s:
                return
        self.clauses.append(sorted(s, key=lambda x: abs(x)))

    def add_unit(self, lit: int):
        self.add_clause([lit])

    def exactly_one(self, vars_: list[int]):
        """Ровно одна переменная из списка истинна."""
        if not vars_:
            raise ValueError("exactly_one получил пустой список")
        self.add_clause(vars_[:])  # хотя бы одна
        for a, b in itertools.combinations(vars_, 2):
            self.add_clause([-a, -b])  # не более одной

    def write_dimacs(self, path: str, comments: bool = True):
        """Сохранить CNF в формате DIMACS."""
        with open(path, "w", encoding="utf-8") as f:
            if comments:
                for var_id in sorted(self.names):
                    f.write(f"c {var_id} {self.names[var_id]}\n")
            f.write(f"p cnf {self.num_vars} {len(self.clauses)}\n")
            for clause in self.clauses:
                f.write(" ".join(map(str, clause)) + " 0\n")

