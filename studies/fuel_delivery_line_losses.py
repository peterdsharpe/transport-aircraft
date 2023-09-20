import aerosandbox as asb
import aerosandbox.numpy as np
from aerosandbox.tools import units as u

lh2_viscosity = (12.84e-6 + 12.53e-6) / 2  # Pa*s, at 22 K, assuming a 50-50 mix of ortho- and para-hydrogen
# According to Liquid Hydrogen Properties, KAERI/TR-2723/2004
# https://www.osti.gov/etdeweb/servlets/purl/20599211, page 26

gh2_viscosity = 1.696e-6  # Pa*s, at 33 K
# Roughly temperature- and pressure-independent, according to
# Liquid Hydrogen Properties, KAERI/TR-2723/2004, page 25 (see above)

lh2_speed_of_sound = 1246  # m/s
gh2_speed_of_sound = 374  # m/s


def get_fanno_parameter(M, gamma):
    """
    Calculate the Fanno parameter given the Mach number M and heat capacity ratio gamma.

    Parameters:
    - M (float): Mach number
    - gamma (float): Heat capacity ratio

    Returns:
    - result (float): Fanno parameter = 4 * f * L / D
    """
    M2 = M ** 2
    term1 = (1 - M2) / (gamma * M2)
    term2 = (gamma + 1) / (2 * gamma)
    term3 = np.log(M2 / ((2 / (gamma + 1)) * (1 + ((gamma - 1) / 2) * M2)))

    result = term1 + term2 * term3
    return result


def get_pipe_analysis(
        mass_flow_rate,
        density,
        viscosity,
        pipe_diameter,
        pipe_length,
        speed_of_sound,
        gamma,
):
    pipe_area = np.pi / 4 * pipe_diameter ** 2

    velocity = mass_flow_rate / (density * pipe_area)

    dynamic_pressure = 0.5 * density * velocity ** 2

    Re = density * velocity * pipe_diameter / viscosity

    friction_factor = 0.316 * Re ** (-0.25)

    # Darcy-Weisbach equation
    pressure_loss = pipe_length * dynamic_pressure / pipe_diameter * friction_factor
    pressure_loss_atm = pressure_loss / u.atm

    ### Compute Fanno properties
    mach = velocity / speed_of_sound
    fanno_parameter = get_fanno_parameter(
        M=mach,
        gamma=gamma
    )

    fanno_length = fanno_parameter * pipe_diameter / 4 / friction_factor

    return locals()

shared_inputs = dict(
    mass_flow_rate = 1 * u.lbm / u.sec,
    pipe_diameter = 1.5 * u.inch,
    pipe_length = 180 * u.ft,
)

lh2_analysis = get_pipe_analysis(
    **shared_inputs,
    density=68.73000,  # at 22 K
    viscosity=lh2_viscosity,
    speed_of_sound=lh2_speed_of_sound,
    gamma=1,
)

gh2_analysis = get_pipe_analysis(
    **shared_inputs,
    density=2.06700,  # at 22 K
    viscosity=gh2_viscosity,
    speed_of_sound=gh2_speed_of_sound,
    gamma=1.4
)

print(f"""\
Liquid Hydrogen Pressure Loss: {lh2_analysis["pressure_loss_atm"]:.3f} atm
Gaseous Hydrogen Pressure Loss: {gh2_analysis["pressure_loss_atm"]:.3f} atm\
""")

import pandas as pd

print(pd.DataFrame(data=[
    lh2_analysis,
    gh2_analysis
], index=[
    "LH2 Flow",
    "GH2 Flow"
]).T.to_markdown())
