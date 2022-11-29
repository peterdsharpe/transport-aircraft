import aerosandbox as asb
import aerosandbox.numpy as np
from aerosandbox.library import aerodynamics as lib_aero
from aerosandbox.tools import units as u
import copy
from typing import Union, Callable, Optional
from libraries import hydrogen

##### Section: Parameters

mission_range = 7500 * u.naut_mile
n_pax = 400

# fuel_type = "Jet A"
fuel_type = "hydrogen"

##### Section: Fuel Properties
if fuel_type == "hydrogen":
    fuel_tank_wall_thickness = 0.0612  # from Brewer, Hydrogen Aircraft Technology pg. 203
    fuel_density = 70  # kg/m^3
    fuel_specific_energy = 119.93e6  # J/kg; lower heating value due to liquid start
    fuel_tank_fuel_mass_fraction = 1 / (1 + 0.356)  # from Brewer, Hydrogen Aircraft Technology pg. 203
elif fuel_type == "Jet A":
    fuel_tank_wall_thickness = 0.005
    fuel_density = 820  # kg/m^3
    fuel_specific_energy = 43.02e6  # J/kg
    fuel_tank_fuel_mass_fraction = 0.95
else:
    raise ValueError("Bad value of `fuel_type`!")

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
fuselage_cabin_xsec_area = np.pi * fuselage_cabin_radius ** 2

fuselage_cabin_length = opti.variable(
    init_guess=123.2 * u.foot,
    lower_bound=1e-3,
    freeze=True,
)
fwd_fuel_tank_length = opti.variable(
    init_guess=6,
    lower_bound=1e-3,
    # freeze=True,
)
aft_fuel_tank_length = fwd_fuel_tank_length

# Compute x-locations of various fuselage stations
nose_fineness_ratio = 1.67
tail_fineness_ratio = 2.62

x_nose = 0
x_nose_to_fwd_tank = x_nose + nose_fineness_ratio * fuselage_cabin_diameter
x_fwd_tank_to_cabin = x_nose_to_fwd_tank + fwd_fuel_tank_length
x_cabin_to_aft_tank = x_fwd_tank_to_cabin + fuselage_cabin_length
x_aft_tank_to_tail = x_cabin_to_aft_tank + aft_fuel_tank_length
x_tail = x_aft_tank_to_tail + tail_fineness_ratio * fuselage_cabin_diameter

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
    # if min_in == 0 and max_in == 1:
    #     f_nondim = f_in
    # else:
    f_nondim = (f_in - min_in) / (max_in - min_in)

    # if max_out == 0 and min_out == 1:
    #     f_out = f_nondim
    # else:
    f_out = f_nondim * (max_out - min_out) + min_out

    return f_out


# Nose
x_sect_nondim = np.sinspace(0, 1, 10)
z_sect_nondim = -0.3 * (1 - x_sect_nondim) ** 2
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
x_sect_nondim = np.linspace(0, 1, 2)
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
x_sect_nondim = np.linspace(0, 1, 2)
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
x_sect_nondim = np.linspace(0, 1, 2)
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
                x_fuse_sections[i],
                0,
                z_fuse_sections[i]
            ],
            radius=r_fuse_sections[i]
        )
        for i in range(np.length(x_fuse_sections))
    ],
    analysis_specific_options={
        asb.AeroBuildup: dict(
            nose_fineness_ratio=nose_fineness_ratio
        )
    }
)

### Wing
wing_airfoil = asb.Airfoil("b737c").repanel(100)
wing_airfoil.generate_polars(
    cache_filename="cache/b737c.json",
    include_compressibility_effects=True,
)

wing_span = opti.variable(
    init_guess=214 * u.foot,
    lower_bound=0,
    freeze=True)
wing_half_span = wing_span / 2

wing_root_chord = opti.variable(
    init_guess=51.5 * u.foot,
    lower_bound=0,
    freeze=True,
)

wing_LE_sweep_deg = opti.variable(
    init_guess=34,
    lower_bound=0,
    freeze=True,
)

wing_yehudi_span_fraction = 0.25
wing_dihedral = 6

# Compute the y locations
wing_yehudi_y = wing_yehudi_span_fraction * wing_half_span
wing_tip_y = wing_half_span

# Compute the x locations
wing_yehudi_x = wing_yehudi_y * np.tand(wing_LE_sweep_deg)
wing_tip_x = wing_tip_y * np.tand(wing_LE_sweep_deg)

# Compute the chords
wing_yehudi_chord = wing_root_chord - wing_yehudi_x
wing_tip_chord = 0.14 * wing_root_chord

# Make the sections
wing_root = asb.WingXSec(
    xyz_le=[0, 0, 0],
    chord=wing_root_chord,
    airfoil=wing_airfoil,
)
wing_yehudi = asb.WingXSec(
    xyz_le=[
        wing_yehudi_x,
        wing_yehudi_y,
        wing_yehudi_y * np.tand(wing_dihedral)
    ],
    chord=wing_yehudi_chord,
    airfoil=wing_airfoil,
)
wing_tip = asb.WingXSec(
    xyz_le=[
        wing_tip_x,
        wing_tip_y,
        wing_tip_y * np.tand(wing_dihedral)
    ],
    chord=wing_tip_chord,
    airfoil=wing_airfoil
)

# Assemble the wing
wing_x_le = opti.variable(
    init_guess=0.5 * x_fwd_tank_to_cabin + 0.5 * x_cabin_to_aft_tank - 0.5 * wing_root_chord,
    freeze=True
)

wing_z_le = -0.5 * fuselage_cabin_radius

wing = asb.Wing(
    name="Main Wing",
    symmetric=True,
    xsecs=[
        wing_root,
        wing_yehudi,
        wing_tip
    ]
).translate([
    wing_x_le,
    0,
    wing_z_le
]).subdivide_sections(3)

### Horizontal Stabilizer
hstab_airfoil = asb.Airfoil("naca0012")
hstab_airfoil.generate_polars(
    cache_filename="cache/naca0012.json",
    include_compressibility_effects=True
)

hstab_span = opti.variable(
    init_guess=70.8 * u.foot,
    lower_bound=0,
    freeze=True
)
hstab_half_span = hstab_span / 2

hstab_root_chord = opti.variable(
    init_guess=23 * u.foot,
    lower_bound=0,
    freeze=True
)

hstab_LE_sweep_deg = opti.variable(
    init_guess=39,
    lower_bound=0,
    freeze=True
)

elevator = asb.ControlSurface(
    name="All-moving Elevator",
    deflection=opti.variable(
        init_guess=0,
        freeze=True
    )
)

hstab_root = asb.WingXSec(
    xyz_le=[0, 0, 0],
    chord=hstab_root_chord,
    airfoil=hstab_airfoil,
    control_surfaces=[
        elevator
    ]
)
hstab_tip = asb.WingXSec(
    xyz_le=[
        hstab_half_span * np.tand(hstab_LE_sweep_deg),
        hstab_half_span,
        0
    ],
    chord=0.35 * hstab_root_chord,
    airfoil=hstab_airfoil
)

# Assemble the hstab
hstab_x_le = x_tail - 2 * hstab_root_chord
hstab_z_le = 0.5 * fuselage_cabin_radius

hstab = asb.Wing(
    name="Horizontal Stabilizer",
    symmetric=True,
    xsecs=[
        hstab_root,
        hstab_tip
    ]
).translate([
    hstab_x_le,
    0,
    hstab_z_le
]).subdivide_sections(3)

### Vertical Stabilizer
vstab_airfoil = asb.Airfoil("naca0008")
vstab_airfoil.generate_polars(
    cache_filename="cache/naca0008.json",
    include_compressibility_effects=True
)

vstab_span = opti.variable(
    init_guess=29.6 * u.foot,
    lower_bound=0,
    freeze=True
)

vstab_root_chord = opti.variable(
    init_guess=22 * u.foot,
    lower_bound=0,
    freeze=True
)

vstab_LE_sweep_deg = opti.variable(
    init_guess=45,
    lower_bound=0,
    freeze=True
)

vstab_root = asb.WingXSec(
    xyz_le=[0, 0, 0],
    chord=vstab_root_chord,
    airfoil=vstab_airfoil
)
vstab_tip = asb.WingXSec(
    xyz_le=[
        vstab_span * np.tand(vstab_LE_sweep_deg),
        0,
        vstab_span,
    ],
    chord=0.35 * vstab_root_chord,
    airfoil=vstab_airfoil
)

# Assemble the vstab
vstab_x_le = x_tail - 2 * vstab_root_chord
vstab_z_le = 1 * fuselage_cabin_radius

vstab = asb.Wing(
    name="Vertical Stabilizer",
    xsecs=[
        vstab_root,
        vstab_tip
    ]
).translate([
    vstab_x_le,
    0,
    vstab_z_le
]).subdivide_sections(3)

### Airplane
airplane = asb.Airplane(
    name="Airplane",
    xyz_ref=[],
    wings=[
        wing,
        hstab,
        vstab
    ],
    fuselages=[
        fuse
    ],
    analysis_specific_options={
        asb.AeroBuildup: dict(
            additional_CD=0.0060
        )
    }
)

##### Section: Vehicle Overall Specs
design_mass_TOGW = opti.variable(
    init_guess=299370,
    lower_bound=0,
    # freeze=True
)

ultimate_load_factor = 1.5 * 2.5

n_engines = 2

LD_estimate = 15
design_climb_rate = 2000 * u.foot / u.minute
g = 9.81
design_V_climb = 250 * u.knot

design_thrust_cruise_total = (
        design_mass_TOGW * g / LD_estimate  # cruise component
)
design_thrust_climb_total = (
        design_thrust_cruise_total +
        design_mass_TOGW * g * design_climb_rate / design_V_climb
)

design_thrust_climb_engine = design_thrust_climb_total / n_engines

mach_cruise = opti.variable(
    init_guess=0.82,
    scale=0.1,
    lower_bound=0,
    upper_bound=1
)
altitude_cruise = opti.variable(
    init_guess=35e3 * u.foot,
    scale=10e3 * u.foot,
    lower_bound=0,
    upper_bound=4e5 * u.foot,
    # freeze=True
)
atmo = asb.Atmosphere(altitude=altitude_cruise)
V_cruise = mach_cruise * atmo.speed_of_sound()

##### Section: Internal Geometry and Weights

mass_props = {}

# Compute useful x stations
x_cabin_midpoint = (x_fwd_tank_to_cabin + x_cabin_to_aft_tank) / 2

# Passenger weight
mass_props["passengers"] = asb.mass_properties_from_radius_of_gyration(
    mass=(215 * u.lbm) * n_pax,
    x_cg=x_cabin_midpoint,
    radius_of_gyration_x=0.5 * fuselage_cabin_radius,
    radius_of_gyration_y=fuselage_cabin_length / 12 ** 0.5,
    radius_of_gyration_z=fuselage_cabin_length / 12 ** 0.5,
)

# Seat weight
mass_props["seats"] = asb.mass_properties_from_radius_of_gyration(
    mass=0.10 * mass_props["passengers"].mass,  # from TASOPT
    x_cg=x_cabin_midpoint,
    radius_of_gyration_x=0.5 * fuselage_cabin_radius,
    radius_of_gyration_y=fuselage_cabin_length / 12 ** 0.5,
    radius_of_gyration_z=fuselage_cabin_length / 12 ** 0.5,
)

# Mass of the auxiliary power unit (APU), from TASOPT.
mass_props["apu"] = asb.mass_properties_from_radius_of_gyration(
    mass=0.035 * mass_props["passengers"].mass,  # from TASOPT
    x_cg=x_cabin_midpoint,
    radius_of_gyration_x=0.5 * fuselage_cabin_radius,
    radius_of_gyration_y=fuselage_cabin_length / 12 ** 0.5,
    radius_of_gyration_z=fuselage_cabin_length / 12 ** 0.5,
)

# Additional payload-proportional weight, from TASOPT:
# "flight attendants, food, galleys, toilets, luggage compartments and furnishings, doors, lighting,
# air conditioning systems, in-flight entertainment systems, etc. These are also assumed
# to be uniformly distributed on average."
mass_props["payload_proportional_weights"] = asb.mass_properties_from_radius_of_gyration(
    mass=0.35 * mass_props["passengers"].mass,  # from TASOPT
    x_cg=x_cabin_midpoint,
    radius_of_gyration_x=0.5 * fuselage_cabin_radius,
    radius_of_gyration_y=fuselage_cabin_length / 12 ** 0.5,
    radius_of_gyration_z=fuselage_cabin_length / 12 ** 0.5,
)

cabin_atmo = asb.Atmosphere(
    altitude=8000 * u.foot  # pressure altitude inside cabin
)

mass_props["buoyancy"] = asb.mass_properties_from_radius_of_gyration(
    mass=(
            (cabin_atmo.density() - atmo.density()) *
            fuselage_cabin_xsec_area * fuselage_cabin_length
    ),
    x_cg=x_cabin_midpoint,
    radius_of_gyration_x=0.5 * fuselage_cabin_radius,
    radius_of_gyration_y=fuselage_cabin_length / 12 ** 0.5,
    radius_of_gyration_z=fuselage_cabin_length / 12 ** 0.5,
)

# Wing/hstab/vstab mass accounting
mass_props["wing"] = asb.mass_properties_from_radius_of_gyration(
    mass=(
                 0.0051 *
                 (design_mass_TOGW / u.lbm * ultimate_load_factor) ** 0.557 *
                 (wing.area() / u.foot ** 2) ** 0.649 *
                 wing.aspect_ratio() ** 0.5 *
                 wing_airfoil.max_thickness() ** -0.4 *
                 (1 + wing.taper_ratio()) ** 0.1 *
                 np.cosd(wing.mean_sweep_angle()) ** -1 *
                 (wing.area() / u.foot ** 2 * 0.1) ** 0.1
         ) * u.lbm,
    x_cg=wing.aerodynamic_center()[0],
    radius_of_gyration_x=wing_span / 12 ** 0.5,
    radius_of_gyration_y=wing_root_chord / 12 ** 0.5,
    radius_of_gyration_z=wing_span / 12 ** 0.5,
)

wing_to_hstab_distance = hstab.aerodynamic_center()[0] - wing.aerodynamic_center()[0]

mass_props["hstab"] = asb.mass_properties_from_radius_of_gyration(
    mass=(
                 0.0379 *
                 1 *
                 (1 + fuselage_cabin_diameter / hstab_span) ** -0.25 *
                 (design_mass_TOGW / u.lbm) ** 0.639 *
                 ultimate_load_factor ** 0.10 *
                 (hstab.area() / u.foot ** 2) ** 0.75 *
                 (wing_to_hstab_distance / u.foot) ** -1 *
                 (0.3 * wing_to_hstab_distance / u.foot) ** 0.704 *
                 np.cosd(hstab.mean_sweep_angle()) ** -1 *
                 hstab.aspect_ratio() ** 0.166 *
                 (1 + 0.1) ** 0.1
         ) * u.lbm,
    x_cg=hstab.aerodynamic_center()[0]
)

wing_to_vstab_distance = vstab.aerodynamic_center()[0] - wing.aerodynamic_center()[0]

mass_props["vstab"] = asb.mass_properties_from_radius_of_gyration(
    mass=(
                 0.0026 *
                 (1 + 0) ** 0.225 *
                 (design_mass_TOGW / u.lbm) ** 0.556 *
                 ultimate_load_factor ** 0.536 *
                 wing_to_vstab_distance ** -0.5 *
                 (vstab.area() / u.foot ** 2) ** 0.5 *
                 (wing_to_vstab_distance / u.foot) ** 0.875 *
                 np.cosd(vstab.mean_sweep_angle()) ** -1 *
                 vstab.aspect_ratio() ** 0.35 *
                 vstab_airfoil.max_thickness() ** -0.5
         ) * u.lbm,
    x_cg=vstab.aerodynamic_center()[0]
)

# Fuselage structure mass
fuselage_structural_length = (x_aft_tank_to_tail - x_nose)
K_ws = (
        0.75 *
        (
                (1 + 2 * wing.taper_ratio()) /
                (1 + wing.taper_ratio())
        ) *
        (
                wing_span / fuselage_structural_length *
                np.tand(wing.mean_sweep_angle())
        )
)  # weight constant from Raymer

mass_props["fuselage"] = asb.mass_properties_from_radius_of_gyration(
    mass=(
                 0.3280 *
                 1.25 *  # 2 cargo doors + 1 aft clamshell door
                 1.0 *  # wing-yehudi-mounted main gear
                 (design_mass_TOGW / u.lbm * ultimate_load_factor) ** 0.5 *
                 (fuselage_structural_length / u.foot) ** 0.25 *
                 (fuse.area_wetted() / u.foot ** 2) ** 0.302 *
                 (1 + K_ws) ** 0.04 *
                 (16) ** 0.10  # L/D
         ) * u.lbm,
    x_cg=x_cabin_midpoint,
    radius_of_gyration_x=0.5 * fuselage_cabin_radius,
    radius_of_gyration_y=fuselage_cabin_length / 12 ** 0.5,
    radius_of_gyration_z=fuselage_cabin_length / 12 ** 0.5,
)

# Engine mass

# Size/weight estimates relative to a GE9X
GE9X_thrust = 110000 * u.lbf
GE9X_fan_diameter = 134 * u.inch
GE9X_outer_diameter = 163.7 * u.inch
GE9X_mass = 21230 * u.lbm
GE9X_TSFC_lb_lb_hour = 0.490  # lb/lb-hr
GE9X_Isp = 3600 / GE9X_TSFC_lb_lb_hour

Isp = GE9X_Isp * (fuel_specific_energy / 43.02e6)

design_max_thrust_ratio_to_GE9X = (
        design_thrust_climb_engine /
        GE9X_thrust
)

engine_fan_diameter = GE9X_fan_diameter * design_max_thrust_ratio_to_GE9X ** 0.5
engine_outer_diameter = GE9X_outer_diameter * design_max_thrust_ratio_to_GE9X ** 0.5
x_engines = wing_x_le + wing_yehudi_x

mass_props["engines"] = asb.mass_properties_from_radius_of_gyration(
    mass=(
            n_engines * GE9X_mass *
            design_max_thrust_ratio_to_GE9X ** 1.1
    ),
    x_cg=x_engines
)

# Landing gear mass
main_landing_gear_length = 1.1 * engine_outer_diameter
main_landing_gear_n_wheels = 6
main_landing_gear_n_shock_struts = 2
main_landing_gear_design_V_stall = 51 * u.knot

mass_props["main_landing_gear"] = asb.mass_properties_from_radius_of_gyration(
    mass=(
                 0.0106 *
                 1 *  # non-kneeling LG
                 (design_mass_TOGW / u.lbm) ** 0.888 *
                 (ultimate_load_factor) ** 0.25 *
                 (main_landing_gear_length / u.inch) ** 0.4 *
                 (main_landing_gear_n_wheels) ** 0.321 *
                 (main_landing_gear_n_shock_struts) ** -0.5 *
                 (main_landing_gear_design_V_stall / u.knot) ** 0.1
         ) * u.lbm,
    x_cg=wing.xsecs[0].xyz_le[0] + wing.xsecs[0].chord
)

nose_landing_gear_length = 0.9 * engine_outer_diameter
nose_landing_gear_n_wheels = 2

mass_props["nose_landing_gear"] = asb.mass_properties_from_radius_of_gyration(
    mass=(
                 0.032 *
                 1 *  # non-reciprocating engine
                 (design_mass_TOGW / u.lbm) ** 0.646 *
                 (ultimate_load_factor) ** 0.2 *
                 (nose_landing_gear_length / u.inch) ** 0.5 *
                 (nose_landing_gear_n_wheels) ** 0.45
         ) * u.lbm,
    x_cg=x_nose_to_fwd_tank
)

# Nacelle mass
nacelle_height = 0.5 * engine_outer_diameter
nacelle_width = 0.2 * engine_outer_diameter
nacelle_length = 0.5 * engine_outer_diameter
mass_engine_and_contents = (
                                   2.331 *
                                   (mass_props["engines"].mass / u.lbm / n_engines) ** 0.901 *
                                   1.0 *  # no propeller
                                   1.18  # thrust reverser
                           ) * u.lbm
nacelle_wetted_area = nacelle_height * nacelle_length * 2.05

mass_props["nacelles"] = asb.mass_properties_from_radius_of_gyration(
    mass=(
            0.6724 *
            1.017 *  # pylon-mounted nacelle
            (nacelle_height / u.foot) ** 0.10 *
            (nacelle_width / u.foot) ** 0.294 *
            (ultimate_load_factor) ** 0.119 *
            (mass_engine_and_contents / u.lbm) ** 0.611 *
            (n_engines) ** 0.984 *
            (nacelle_wetted_area / u.foot ** 2) ** 0.224
    )
)
mass_props["engine_controls"] = asb.mass_properties_from_radius_of_gyration(
    mass=(
                 5 * n_engines +
                 0.80 * (x_cabin_midpoint / u.foot) * n_engines
         ) * u.lbm,
    x_cg=(x_engines + x_nose) / 2,
)

mass_props["starter"] = asb.mass_properties_from_radius_of_gyration(
    mass=(
                 49.19 * (
                 mass_props["engines"].mass / u.lbm
                 / 1000
         ) ** 0.541
         ) * u.lbm,
    x_cg=x_engines
)

control_surface_area = 0.15 * (
        wing.area() +
        hstab.area() +
        vstab.area()
)
control_surface_sizing_Iyy_aircraft = (
        design_mass_TOGW * wing_to_hstab_distance ** 2
)

mass_props["flight_controls"] = asb.mass_properties_from_radius_of_gyration(
    mass=(
                 145.9 *
                 6 ** 0.554 *  # number of functions performed by controls
                 (1 + 1 / 6) ** -1 *
                 (control_surface_area / u.foot ** 2) ** 0.20 *
                 (control_surface_sizing_Iyy_aircraft / (u.lbm * u.foot ** 2) * 1e-6) ** 0.07
         ) * u.lbm,
    x_cg=(
            0.5 * wing.aerodynamic_center()[0] +
            0.3 * hstab.aerodynamic_center()[0] +
            0.2 * vstab.aerodynamic_center()[0]
    )
)

n_crew = 2

mass_props["instruments"] = asb.mass_properties_from_radius_of_gyration(
    mass=(
                 4.509 *
                 1 *  # non-reciprocating
                 1 *  # not turboprop
                 n_crew ** 0.541 *
                 n_engines * (fuselage_cabin_length / u.foot * wing_span / u.foot) ** 0.5
         ) * u.lbm,
    x_cg=x_nose_to_fwd_tank
)

mass_props["hydraulics"] = asb.mass_properties_from_radius_of_gyration(
    mass=(
                 0.2673 *
                 6 *
                 (fuselage_cabin_length / u.foot * wing_span / u.foot) ** 0.937
         ) * u.lbm,
    x_cg=wing.xsecs[0].xyz_le[0] + wing.xsecs[0].chord
)

mass_props["electrical"] = asb.mass_properties_from_radius_of_gyration(
    mass=(
                 7.291 *
                 48 ** 0.782 *  # voltage
                 (fuselage_cabin_length / u.foot) ** 0.346 *
                 (n_engines) ** 0.10
         ) * u.lbm,
    x_cg=x_engines
)

mass_props["avionics"] = asb.mass_properties_from_radius_of_gyration(
    mass=(
                 1.73 *
                 (1100) ** 0.983
         ) * u.lbm,
    x_cg=x_nose_to_fwd_tank
)

mass_props["anti-ice"] = asb.mass_properties_from_radius_of_gyration(
    mass=0.002 * design_mass_TOGW,
    x_cg=wing.aerodynamic_center()[0]
)

mass_props["handling_gear"] = asb.mass_properties_from_radius_of_gyration(
    mass=3e-4 * design_mass_TOGW,
    x_cg=x_cabin_midpoint
)

# Fuel tank weights
fwd_fuel_tank_exterior_volume = fuselage_cabin_xsec_area * fwd_fuel_tank_length
aft_fuel_tank_exterior_volume = fuselage_cabin_xsec_area * aft_fuel_tank_length

fuel_tank_tank_mass_fraction = 1 - fuel_tank_fuel_mass_fraction

fuel_tank_interior_radius = fuselage_cabin_radius - fuel_tank_wall_thickness
fuel_tank_xsec_area = np.pi * fuel_tank_interior_radius ** 2

fwd_fuel_tank_interior_volume = fuel_tank_xsec_area * (fwd_fuel_tank_length - 2 * fuel_tank_wall_thickness)
aft_fuel_tank_interior_volume = fuel_tank_xsec_area * (aft_fuel_tank_length - 2 * fuel_tank_wall_thickness)

x_fwd_tank_midpoint = (x_nose_to_fwd_tank + x_fwd_tank_to_cabin) / 2
x_aft_tank_midpoint = (x_cabin_to_aft_tank + x_aft_tank_to_tail) / 2

mass_props_full_fuel_fwd = asb.mass_properties_from_radius_of_gyration(
    mass=fuel_density * fwd_fuel_tank_interior_volume,
    x_cg=x_fwd_tank_midpoint
)
mass_props_full_fuel_aft = asb.mass_properties_from_radius_of_gyration(
    mass=fuel_density * aft_fuel_tank_interior_volume,
    x_cg=x_aft_tank_midpoint
)

mass_props["fuel"] = mass_props_full_fuel_fwd + mass_props_full_fuel_aft

mass_props["tanks"] = mass_props["fuel"] / fuel_tank_fuel_mass_fraction * fuel_tank_tank_mass_fraction

# Compute empty mass
mass_props_empty = asb.MassProperties(mass=0)
for k, v in mass_props.items():
    if k == "passengers" or k == "fuel":
        continue
    else:
        mass_props_empty = mass_props_empty + v

mass_props_empty_fuselage = mass_props_empty - (
        mass_props['wing'] +
        mass_props['hstab'] +
        mass_props['vstab']
)

### Compute all-up mass
mass_props_with_pax = mass_props_empty + mass_props["passengers"]
mass_props_TOGW = mass_props_with_pax + mass_props["fuel"]
mass_props_half_fuel = mass_props_with_pax + mass_props["fuel"] * 0.5

### Constrain mass closure
opti.subject_to([
    mass_props_TOGW.mass < design_mass_TOGW
])

##### Section: Dynamics
dyn = asb.DynamicsPointMass2DSpeedGamma(
    mass_props=mass_props_half_fuel,
    x_e=0,
    z_e=-altitude_cruise,
    speed=V_cruise,
    gamma=0,
    alpha=opti.variable(
        init_guess=10,
        lower_bound=0,
        upper_bound=15
    ),
)

##### Section: Aerodynamics

aero = asb.AeroBuildup(
    airplane=airplane,
    op_point=dyn.op_point,
    xyz_ref=mass_props_half_fuel.xyz_cg
).run()

opti.subject_to([
    aero["L"] / 1e6 == g * mass_props_half_fuel.mass / 1e6
])

LD = aero["L"] / aero["D"]

##### Section: Compute Range
flight_range = (
        V_cruise *
        LD *
        Isp *
        np.log(
            mass_props_TOGW.mass / mass_props_with_pax.mass
        )
)

# TODO add boiloff

opti.subject_to([
    flight_range / mission_range > 1
])

##### Section: Finalize Optimization Problem
# opti.minimize(design_mass_TOGW)
opti.minimize(fwd_fuel_tank_length)

if __name__ == '__main__':
    try:
        sol = opti.solve()
    except RuntimeError:
        sol = opti.debug
    s = lambda x: sol.value(x)

    airplane.substitute_solution(sol)
    dyn.substitute_solution(sol)

    for v in mass_props.values():
        v.substitute_solution(sol)

    import matplotlib.pyplot as plt
    import aerosandbox.tools.pretty_plots as p

    ##### Section: Printout
    print_title = lambda s: print(s.upper().join(["*" * 20] * 2))

    print_title("Outputs")
    for k, v in {
        "flight_range_nmi"    : flight_range / u.naut_mile,
        "mass_fuel_per_pax_mi": mass_props["fuel"].mass / (n_pax * (flight_range / u.naut_mile)),
        "L/D"                 : LD,
    }.items():
        print(f"{k.rjust(25)} = {s(v):.6g}")

    print_title("Key design variables")
    for k, v in {
        "fwd_fuel_tank_length"   : fwd_fuel_tank_length,
        "fuselage_cabin_diameter": fuselage_cabin_diameter,
        "mass_TOGW"              : mass_props_TOGW.mass,
        "mass_empty"             : mass_props_empty.mass,
        "mach_cruise"            : mach_cruise,
        "altitude_cruise"        : altitude_cruise,
        "alpha"                  : dyn.alpha,
    }.items():
        print(f"{k.rjust(25)} = {s(v):.6g}")

    print_title("Mass props")
    for k, v in mass_props.items():
        print(f"{k.rjust(25)} = {v.mass:.0f} kg")

    ##### Section: Aero Polar

    op_point_polar = copy.deepcopy(dyn.op_point)
    op_point_polar.alpha = np.linspace(-15, 15, 50)

    aero_polar = asb.AeroBuildup(
        airplane=airplane,
        op_point=op_point_polar,
        xyz_ref=mass_props_half_fuel.xyz_cg
    ).run()
    aero_polar["alpha"] = op_point_polar.alpha

    fig, ax = plt.subplots()
    plt.plot(aero_polar["alpha"], aero_polar["CL"] / aero_polar["CD"])
    p.show_plot(
        "Aerodynamic Efficiency Polar",
        r"Angle of Attack $\alpha$ [deg]",
        r"Lift / Drag [-]"
    )

    ##### Section: Mass Budget
    fig, ax = plt.subplots(figsize=(10, 6), subplot_kw=dict(aspect="equal"), dpi=300)

    name_remaps = {
        "apu"                         : "APU",
        "wing"                        : "Wing Structure",
        "hstab"                       : "H-Stab Structure",
        "vstab"                       : "V-Stab Structure",
        "fuselage"                    : "Fuselage Structure",
        "payload_proportional_weights": "FAs, Food, Galleys, Lavatories,\nLuggage Hold, Doors, Lighting,\nAir Cond., Entertainment"
    }


    def get_name(s):
        if s in name_remaps:
            return name_remaps[s]
        else:
            return s.replace("_", " ").title()


    pie = {
        get_name(k): v.mass
        for k, v in mass_props.items()
    }
    colors = p.sns.color_palette("husl", n_colors=len(pie))


    def pie_format(name: str, value: float):
        pct = value / s(mass_props_TOGW.mass) * 100
        joiner = ", " if len(name) < 20 else "\n"
        if pct > 0.5:
            data = f"{value:.0f} kg, {pct:.0f}%"
        else:
            data = f"{value:.0f} kg"

        label = name + joiner + data
        return label


    pie_labels = [
        pie_format(k, v)
        for k, v in pie.items()
    ]

    wedges, texts = ax.pie(
        list(pie.values()),
        colors=colors,
        startangle=90,
        wedgeprops=dict(
            width=0.5
        )
    )

    kw = dict(
        arrowprops=dict(arrowstyle="-", color="k"),
        zorder=0,
        va="center"
    )

    for w in wedges:
        w.theta_mid = (w.theta2 - w.theta1) / 2. + w.theta1
        w.x_pie = np.cos(np.deg2rad(w.theta_mid))
        w.y_pie = np.sin(np.deg2rad(w.theta_mid))
        w.is_right = w.x_pie > 0

    left_wedges = []
    right_wedges = []
    for w in wedges:
        if w.is_right:
            right_wedges.append(w)
        else:
            left_wedges.append(w)

    y_texts_left = 1.4 * np.linspace(-1, 1, len(left_wedges))
    y_texts_right = 1.4 * np.linspace(-1, 1, len(right_wedges))

    left_wedge_order = np.argsort([w.y_pie for w in left_wedges])
    for i, w in enumerate(np.array(left_wedges, "O")[left_wedge_order]):
        w.y_text = y_texts_left[i]

    right_wedge_order = np.argsort([w.y_pie for w in right_wedges])
    for i, w in enumerate(np.array(right_wedges, "O")[right_wedge_order]):
        w.y_text = y_texts_right[i]

    for i, w in enumerate(wedges):
        ang = (w.theta2 - w.theta1) / 2. + w.theta1
        x_pie = np.cos(np.deg2rad(ang))
        y_pie = np.sin(np.deg2rad(ang))
        x_text = 1.2 * np.sign(x_pie)
        kw["arrowprops"].update(dict(
            connectionstyle=f"arc,angleA={180 if w.is_right else 0},angleB={ang},armA=40,armB=40,rad=20",
            relpos=(0 if w.is_right else 1, 0.5)
        ))
        ax.annotate(
            pie_labels[i],
            xy=(w.x_pie, w.y_pie),
            xytext=(x_text, w.y_text),
            horizontalalignment="left" if w.is_right else "right",
            **kw
        )

    plt.text(
        x=0,
        y=0,
        s=f"$\\bf{{Mass\\ Budget}}$\nTOGW: {s(mass_props_TOGW.mass):.0f} kg\nOEW: {s(mass_props_empty.mass):.0f} kg",
        ha="center",
        va="center",
        fontsize=16,
    )
    p.show_plot(savefig="figures/mass_budget.png")

    ##### Section: Payload-Range diagram
