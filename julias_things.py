# from design_opt import *
import colebrook
### Upstream dependencies
transport_efficiency_MJ_per_seat_km = 0.008 # kg/seat-km

### My calculations

## Constants
hydrogen_density = 70 #kg/m^3
hydrogen_dynamic_viscosity = 1.4E-5 #Pa*s
pipe_roughness = 0.045 #mm
## Pipe flow losses
# Pipe Design
pipe_length = 10 #m
pipe_diameter = 0.5 #m
mass_flow_rate = 50 #kg/s
#Intermediate values
pipe_area = 3.1415*(pipe_diameter/2)**2 #m^2
volume_flow_rate = mass_flow_rate/hydrogen_density #m^3/s
speed = volume_flow_rate/pipe_area #m/s
#Friction Factor Calculation
Re = speed*pipe_diameter*hydrogen_density/hydrogen_dynamic_viscosity
relative_roughness = pipe_roughness/1000/pipe_diameter
darcy_friction_factor = colebrook.sjFriction( Re, relative_roughness)
#Solution
dP = pipe_length*darcy_friction_factor*hydrogen_density*(1/2)/pipe_diameter*speed**2 #Pa
dH = dP/9.81/hydrogen_density #m, head loss
print(dP, darcy_friction_factor)