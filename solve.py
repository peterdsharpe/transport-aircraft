from design_opt import *

try:
    sol = opti.solve()
except RuntimeError:
    sol = opti.debug
s = lambda x: sol.value(x)

airplane = sol(airplane)
dyn = sol(dyn)
mass_props = sol(mass_props)