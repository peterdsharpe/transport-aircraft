from design_opt import *

try:
    sol = opti.solve()
except RuntimeError:
    sol = opti.debug
s = lambda x: sol.value(x)

airplane.substitute_solution(sol)
dyn.substitute_solution(sol)

for v in mass_props.values():
    v.substitute_solution(sol)
