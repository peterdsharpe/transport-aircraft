# from design_opt import *

### Upstream dependencies
transport_efficiency_MJ_per_seat_km = 0.008 # kg/seat-km

### My calculations

## Constants
hydrogen_density = 70 #kg/m^3
hydrogen_dynamic_viscosity = 1.4E-5 #Pa*s
pipe_roughness = 0.045 #mm
## Pipe flow losses
pipe_length = 2 #m
pipe_diameter = 0.5 #m
mass_flow_rate = 50 #kg/s

pipe_area = pi*(pipe_diameter/2)^2
volume_flow_rate = mass_flow_rate/hydrogen_density #m^3/s
speed = volume_flow_rate/pipe_area
Re = speed*pipe_diameter*hydrogen_density/hydrogen_dynamic_viscosity



