import numpy as np

from design_opt_variable_gravimetric_efficiency import *
from study_colors import lh2_color, kerosene_color

vals = np.sinspace(0.2221, 1, 21)[::-1]

get_sols = opti.solve_sweep(
    parameter_mapping={
        fuel_tank_fuel_mass_fraction: vals
    },
    solve_kwargs=dict(
        max_iter=50,
    ),
    update_initial_guesses_between_solves=True,
    return_callable=True
)

import matplotlib.pyplot as plt
import aerosandbox.tools.pretty_plots as p

fig, ax = plt.subplots(
    figsize=(5.8, 4.5)
)

mask = np.logical_not(np.isnan(get_sols(transport_efficiency_MJ_per_seat_km)))

p.plot_smooth(
    vals[mask],
    get_sols(transport_efficiency_MJ_per_seat_km)[mask],
    "-",
    color=lh2_color,
    linewidth=2,
    zorder=4,
)

point_design = (1 / (1 + 0.356), 0.904179)

plt.plot(
    [point_design[0]],
    [point_design[1]],
    ".",
    color=p.adjust_lightness(lh2_color, 0.5),
    zorder=5,
)

plt.annotate(
    text="LH2 Point Design\n\"Best Guess\"",
    xy=point_design,
    xytext=(20, 40),
    xycoords="data",
    textcoords="offset points",
    ha="center",
    va="bottom",
    fontsize=11,
    color=p.adjust_lightness(lh2_color, 0.5),
    alpha=0.7,
    arrowprops={
        "color"     : p.adjust_lightness(lh2_color, 0.5),
        "alpha"     : 0.5,
        "width"     : 0.25,
        "headwidth" : 4,
        "headlength": 6,
        "connectionstyle":"angle3,angleA=0,angleB=-90",
        "shrink"   : 0.1,
    },
    zorder=5,
)

plt.fill_between(
    x=[0, 1],
    y1=0.84,
    y2=1.13,
    color=kerosene_color,
    alpha=0.25
)
plt.annotate(
    text="Typical range for kerosene aircraft"
         "\n(B777-300ER: 0.84 - 1.13 MJ / pax-km)",
    xy=(0.02, 0.86),
    xytext=(0, 0),
    xycoords="data",
    textcoords="offset points",
    ha="left",
    va="bottom",
    fontsize=10,
    color=p.adjust_lightness(kerosene_color, 0.5),
    alpha=0.7

)

from matplotlib import ticker

ax.xaxis.set_major_formatter(ticker.PercentFormatter(1))

plt.xlim(0, 1)
plt.ylim(0, 2)
p.set_ticks(0.25, 0.05, 0.5, 0.1)

for l, t in {
    "top": "Less Efficient",
    "bot": "More Efficient",
}.items():
    plt.annotate(
        text=t,
        xy=(0.125, 1.9 if l == "top" else 0.1),
        xytext=(0, -30 if l == "top" else 30),
        xycoords="data",
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

plt.suptitle("LH2 Tank Fuel Fraction vs. Required Transport Energy", y=0.95)
plt.title("400 pax, 7,500 nmi mission", color="gray")

p.show_plot(
    # "LH2 Tank Fuel Fraction vs. Transport Efficiency",
    None,
    r"Fuel Tank Gravimetric Efficiency $\eta_{\mathrm{tank}} = \frac{m_\mathrm{fuel}}{m_\mathrm{fuel} + m_\mathrm{tank}}$",
    "Transport Energy\n[MJ / passenger-km]",
    dpi=600,
)
