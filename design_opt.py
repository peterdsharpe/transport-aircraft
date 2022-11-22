import aerosandbox as asb
import aerosandbox.numpy as np
from aerosandbox.library import aerodynamics as lib_aero
from aerosandbox.tools import units as u
import copy
from typing import Union, Callable, Optional
from libraries import hydrogen

##### Section: Parameters

range = 8000 * u.naut_mile
n_pax = 400

##### Section: Initialize Optimization

opti = asb.Opti(
    freeze_style='float'
)

##### Section: Vehicle Definition

"""
Coordinate system:

Geometry axes. Datum is:
    * x=0 is set at the YZ plane coincident with the nose of the airplane.
    * y=0 and z=0 are both set by the centerline of the fuselage.
    
Note that the nose of the airplane is slightly below (-z) the centerline of the fuselage.
"""

### Fuselage

fuselage_cabin_diameter = opti.variable(
    init_guess=20.4 * u.foot,
    lower_bound=1e-3,
    freeze=True,
)
fuselage_cabin_radius = fuselage_cabin_diameter / 2
fuselage_cabin_length = opti.variable(
    init_guess=123.2 * u.foot,
    lower_bound=1e-3,
    freeze=True,
)
fwd_fuel_tank_length = opti.variable(
    init_guess=3,
    lower_bound=1e-3,
    freeze=True,
)
aft_fuel_tank_length = fwd_fuel_tank_length

# Compute x-locations of various fuselage stations
x_nose = 0
x_nose_to_fwd_tank = x_nose + 1.67 * fuselage_cabin_diameter
x_fwd_tank_to_cabin = x_nose_to_fwd_tank + fwd_fuel_tank_length
x_cabin_to_aft_tank = x_fwd_tank_to_cabin + fuselage_cabin_length
x_aft_tank_to_tail = x_cabin_to_aft_tank + aft_fuel_tank_length
x_tail = x_aft_tank_to_tail + 2.62 * fuselage_cabin_diameter

# Build up the actual fuselage nodes
x_fuse_sections = []
z_fuse_sections = []
r_fuse_sections = []


def linear_map(
        f_in: Union[float, np.ndarray],
        min_in: Union[float, np.ndarray],
        max_in: Union[float, np.ndarray],
        min_out: Union[float, np.ndarray],
        max_out: Union[float, np.ndarray],
) -> Union[float, np.ndarray]:
    """
    Linearly maps an input `f_in` from range (`min_in`, `max_in`) to (`min_out`, `max_out`).

    Args:
        f_in: Input value
        min_in:
        max_in:
        min_out:
        max_out:

    Returns:
        f_out: Output value

    """
    if min_in == 0 and max_in == 1:
        f_nondim = f_in
    else:
        f_nondim = (f_in - min_in) / (max_in - min_in)

    if max_out == 0 and min_out == 1:
        f_out = f_nondim
    else:
        f_out = f_nondim * (max_out - min_out) + min_out

    return f_out


# Nose
x_sect_nondim = np.sinspace(0, 1, 10)
z_sect_nondim = -0.4 * (1 - x_sect_nondim) ** 2
r_sect_nondim = (1 - (1 - x_sect_nondim) ** 2) ** 0.5

x_fuse_sections.append(
    linear_map(
        f_in=x_sect_nondim,
        min_in=0, max_in=1,
        min_out=x_nose, max_out=x_nose_to_fwd_tank
    )
)
z_fuse_sections.append(
    linear_map(
        f_in=z_sect_nondim,
        min_in=0, max_in=1,
        min_out=0, max_out=fuselage_cabin_radius
    )
)
r_fuse_sections.append(
    linear_map(
        f_in=r_sect_nondim,
        min_in=0, max_in=1,
        min_out=0, max_out=fuselage_cabin_radius
    )
)

# Fwd tank
x_sect_nondim = np.linspace(0, 1, 10)
z_sect_nondim = np.zeros_like(x_sect_nondim)
r_sect_nondim = np.ones_like(x_sect_nondim)

x_fuse_sections.append(
    linear_map(
        f_in=x_sect_nondim,
        min_in=0, max_in=1,
        min_out=x_nose_to_fwd_tank, max_out=x_fwd_tank_to_cabin
    )
)
z_fuse_sections.append(
    linear_map(
        f_in=z_sect_nondim,
        min_in=0, max_in=1,
        min_out=0, max_out=fuselage_cabin_radius
    )
)
r_fuse_sections.append(
    linear_map(
        f_in=r_sect_nondim,
        min_in=0, max_in=1,
        min_out=0, max_out=fuselage_cabin_radius
    )
)

# Cabin
x_sect_nondim = np.linspace(0, 1, 10)
z_sect_nondim = np.zeros_like(x_sect_nondim)
r_sect_nondim = np.ones_like(x_sect_nondim)

x_fuse_sections.append(
    linear_map(
        f_in=x_sect_nondim,
        min_in=0, max_in=1,
        min_out=x_fwd_tank_to_cabin, max_out=x_cabin_to_aft_tank
    )
)
z_fuse_sections.append(
    linear_map(
        f_in=z_sect_nondim,
        min_in=0, max_in=1,
        min_out=0, max_out=fuselage_cabin_radius
    )
)
r_fuse_sections.append(
    linear_map(
        f_in=r_sect_nondim,
        min_in=0, max_in=1,
        min_out=0, max_out=fuselage_cabin_radius
    )
)

# Aft Tank
x_sect_nondim = np.linspace(0, 1, 10)
z_sect_nondim = np.zeros_like(x_sect_nondim)
r_sect_nondim = np.ones_like(x_sect_nondim)

x_fuse_sections.append(
    linear_map(
        f_in=x_sect_nondim,
        min_in=0, max_in=1,
        min_out=x_cabin_to_aft_tank, max_out=x_aft_tank_to_tail
    )
)
z_fuse_sections.append(
    linear_map(
        f_in=z_sect_nondim,
        min_in=0, max_in=1,
        min_out=0, max_out=fuselage_cabin_radius
    )
)
r_fuse_sections.append(
    linear_map(
        f_in=r_sect_nondim,
        min_in=0, max_in=1,
        min_out=0, max_out=fuselage_cabin_radius
    )
)

# Tail
x_sect_nondim = np.linspace(0, 1, 10)
z_sect_nondim = 1 * x_sect_nondim ** 1.5
r_sect_nondim = 1 - x_sect_nondim ** 1.5

x_fuse_sections.append(
    linear_map(
        f_in=x_sect_nondim,
        min_in=0, max_in=1,
        min_out=x_aft_tank_to_tail, max_out=x_tail
    )
)
z_fuse_sections.append(
    linear_map(
        f_in=z_sect_nondim,
        min_in=0, max_in=1,
        min_out=0, max_out=fuselage_cabin_radius
    )
)
r_fuse_sections.append(
    linear_map(
        f_in=r_sect_nondim,
        min_in=0, max_in=1,
        min_out=0, max_out=fuselage_cabin_radius
    )
)

# Compile Fuselage
x_fuse_sections = np.concatenate([
    x_fuse_section[:-1] if i != len(x_fuse_sections) - 1 else x_fuse_section
    for i, x_fuse_section in enumerate(x_fuse_sections)
])
z_fuse_sections = np.concatenate([
    z_fuse_section[:-1] if i != len(z_fuse_sections) - 1 else z_fuse_section
    for i, z_fuse_section in enumerate(z_fuse_sections)
])
r_fuse_sections = np.concatenate([
    r_fuse_section[:-1] if i != len(r_fuse_sections) - 1 else r_fuse_section
    for i, r_fuse_section in enumerate(r_fuse_sections)
])

fuse = asb.Fuselage(
    name="Fuselage",
    xsecs=[
        asb.FuselageXSec(
            xyz_c=[
                x,
                0,
                z
            ],
            radius=r
        )
        for x, z, r in zip(
            x_fuse_sections,
            z_fuse_sections,
            r_fuse_sections
        )
    ]
)
