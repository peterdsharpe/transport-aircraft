# from design_opt import *
import colebrook
### Upstream dependencies
transport_efficiency_MJ_per_seat_km = 0.008 # kg/seat-km

### My calculations
## Constants
hydrogen_density = 70 #kg/m^3
hydrogen_dynamic_viscosity = 1.4E-5 #Pa*s
pipe_roughness = 0.045 #mm
def pipe_losses(length, diameter, mass_flow_rate):
    #Intermediate values
    pipe_area = 3.1415*(diameter/2)**2 #m^2
    volume_flow_rate = mass_flow_rate/hydrogen_density #m^3/s
    speed = volume_flow_rate/pipe_area #m/s
    #Friction Factor Calculation
    Re = speed*diameter*hydrogen_density/hydrogen_dynamic_viscosity
    relative_roughness = pipe_roughness/1000/pipe_diameter
    darcy_friction_factor = colebrook.bntFriction( Re, relative_roughness)
    #Solution
    dP = length*darcy_friction_factor*hydrogen_density*(1/2)/diameter*speed**2 #Pa
    dH = dP/9.81/hydrogen_density #m, head loss
    print("Pressure Drop: ", dP, " | Head Loss: ", dH, " | Friction Factor: ", darcy_friction_factor)
    return dP, dH

## Pipe flow losses
# Pipe Design
pipe_length = 10 #m
pipe_diameter = 0.5 #m
refueling_time = 9.81 #min
fueling_flow_rate = 50 #kg/s
[dP, dH] = pipe_losses(pipe_length, pipe_diameter, fueling_flow_rate)
pump_power_refueling = (dH + pipe_length)*fueling_flow_rate*9.81 #W
[dP, dH] = pipe_losses(19000, 0.4, fueling_flow_rate)
pump_power_pipeline = dH*fueling_flow_rate*9.81 #W
pump_power_hp = pump_power_pipeline/746 #hp
print("Pump Power [hp]: ", pump_power_hp)

energy_demand_ORD = 130*10**6*.7/3.6 #kWh/day
energy_demand_pipeline = pump_power_pipeline*24/1000 #kWh/day
energy_demand_fueling = pump_power_refueling*refueling_time/60/1000*54 #kWh/day
pipeline_energy_percent = energy_demand_pipeline/(energy_demand_ORD+energy_demand_fueling + energy_demand_pipeline)*100
fueling_energy_percent = energy_demand_fueling/(energy_demand_ORD+energy_demand_fueling + energy_demand_pipeline)*100
print("Pipeline Pump Energy Percent of Total Energy Required: ", pipeline_energy_percent)
print("Fueling Pump Energy Percent of Total Energy Required: ", fueling_energy_percent)