import aerosandbox as asb
import aerosandbox.numpy as np
from aerosandbox.tools import units as u
from design_opt_wrapped import get_problem


def get_market_coverage(
        fuel_type="kerosene",
        design_range=7500 * u.naut_mile
):
    print(f"{fuel_type}, {design_range / u.naut_mile} nmi")

    vars = get_problem(
        fuel_type=fuel_type,
    )
    opti: asb.Opti = vars["opti"]
    sol = opti.solve(
        parameter_mapping={
            vars["mission_range"]: design_range
        }
    )

    mass_props = sol(vars["mass_props"])
    mass_props_empty = sol(vars["mass_props_empty"])

    ##### Get the market coverage

    empty_weight = mass_props_empty.mass
    total_pax_weight = mass_props["passengers"].mass
    total_fuel_weight = mass_props["fuel"].mass

    ### First, full pax load until the design range
    fuel_frac = np.linspace(1e-3, 1, 100)
    fuel_weights = total_fuel_weight * fuel_frac

    flight_ranges_sub = sol(
        vars["V_cruise"] *
        vars["LD_cruise"] *
        vars["Isp"] *
        np.log(
            (empty_weight + total_pax_weight + fuel_weights) /
            (empty_weight + total_pax_weight)
        )
    )

    transport_efficiencies_sub = sol(
        fuel_weights * vars["fuel_specific_energy"] / (
                vars["n_pax"] * flight_ranges_sub
        ) / (1e6 / 1e3)
    )

    ### Then, beyond the design range, start unloading pax
    pax_frac = np.linspace(1e-3, 1, 100)[::-1]
    pax_weights = total_pax_weight * pax_frac

    flight_ranges_sup = sol(
        vars["V_cruise"] *
        vars["LD_cruise"] *
        vars["Isp"] *
        np.log(
            (empty_weight + pax_weights + total_fuel_weight) /
            (empty_weight + pax_weights)
        )
    )

    transport_efficiencies_sup = sol(
        total_fuel_weight * vars["fuel_specific_energy"] / (
                pax_frac * vars["n_pax"] * flight_ranges_sup
        ) / (1e6 / 1e3)
    )

    ### Merge
    flight_ranges = np.concatenate(
        [flight_ranges_sub, flight_ranges_sup]
    )
    transport_efficiencies = np.concatenate(
        [transport_efficiencies_sub, transport_efficiencies_sup]
    )

    return flight_ranges, transport_efficiencies


fuel_types = ["kerosene", "LH2"]
design_ranges = np.array([2000, 3750, 5500, 7500]) * u.naut_mile

if "data" not in locals():
    data = {
        fuel_type: {
            design_range: get_market_coverage(
                fuel_type=fuel_type,
                design_range=design_range
            )
            for design_range in design_ranges
        }
        for fuel_type in fuel_types
    }

import matplotlib.pyplot as plt
import aerosandbox.tools.pretty_plots as p

fig, ax = plt.subplots(
    figsize=(4.8, 4.3)
)

lh2_color = "deepskyblue"
kerosene_color = "darkorange"

to_plot = [
    ("kerosene", 7500 * u.naut_mile),
    # ("kerosene", 5000 * u.naut_mile),
    ("kerosene", 3750 * u.naut_mile),
    # ("kerosene", 2500 * u.naut_mile),
    ("LH2", 7500 * u.naut_mile),
    # ("LH2", 5500 * u.naut_mile),
    ("LH2", 3750 * u.naut_mile),
    # ("LH2", 2000 * u.naut_mile),
]

for fuel_type, design_range in to_plot:
    color = p.adjust_lightness(
            color=kerosene_color if fuel_type == "kerosene" else lh2_color,
            amount=(design_range / (5000 * u.naut_mile)) ** -0.5 - 0.2
        )

    x, y = data[fuel_type][design_range]

    plt.plot(
        x / u.naut_mile,
        y,
        color=color,
        alpha=0.8,
        linewidth=2,
    )
    plt.fill_between(
        x / u.naut_mile,
        y,
        1e30,
        color=color,
        alpha=0.1,
    )
    plt.plot(
        [design_range / u.naut_mile],
        [y[np.argmin((x - design_range) ** 2)]],
        ".",
        color=color,
    )

    if fuel_type == "kerosene":
        names = {
            3750 * u.naut_mile: "B737-class",
            7500 * u.naut_mile: "B777-class",
        }
        for d, n in names.items():
            if design_range == d:
                plt.annotate(
                    text=n,
                    xy=(design_range / u.naut_mile, y[np.argmin((x - design_range) ** 2)]),
                    xytext=(0, -8),
                    textcoords="offset points",
                    ha="center",
                    va="top",
                    color=p.adjust_lightness(color, 0.5),
                    fontsize=11,
                )

plt.xlim(0, 10000)
plt.ylim(0, 1.25)
p.set_ticks(2500, 500, 0.25, 0.05)

for l, t in {
    "top": "Less Efficient",
    "bot": "More Efficient",
}.items():
    plt.annotate(
        text=t,
        xy=(0.15, 0.94 if l == "top" else 0.06),
        xytext=(0, -30 if l == "top" else 30),
        xycoords="axes fraction",
        textcoords="offset points",
        ha="center",
        va="center",
        color="gray",
        fontsize=11,
        arrowprops={
            "color"     : "gray",
            "width"     : 0.25,
            "headwidth" : 4,
            "headlength": 6,
        }
    )

plt.plot(
    [], [], "-", color="gray",
    label="Each line is a unique airplane"
)

plt.legend(
    loc="upper right"
)

p.show_plot(
    # "LH2 Tank Fuel Fraction vs. Transport Efficiency",
    # None,
    "Off-Design Transport Efficiency and Market Coverage",
    r"Mission Range [nmi]",
    "Transport Energy\n[MJ / passenger-km]",
    legend=False,
    dpi=600,
)
