import pandas as pd
from io import StringIO

def parse_table(data_string:str):

    # Remove the first three lines which contain meta information and are not part of the actual data
    clean_data = "\n".join(data_string.split('\n')[3:])

    # Define column names
    columns = [
        "Temperature_K", "Temperature_C", "Temperature_F",
        "Pressure_MPa", "Pressure_bara", "Pressure_psia",
        "Density_mol_dm3", "Density_g_l", "Density_kg_m3",
        "Specific_weight_lbm_ft3", "Specific_weight_sl_ft3_10_minus_3",
        "Specific_weight_N_m3", "Specific_weight_lbf_ft3"
    ]

    # Read the data into a Pandas DataFrame
    df = pd.read_csv(StringIO(clean_data), delim_whitespace=True, names=columns)

    # Remove the first row which contains invalid data ("Liquid at equilibrium pressure")
    df = df.iloc[1:].reset_index(drop=True)

    # Convert all columns to float for numerical operations
    df = df.astype(float)

    return df

data_liquid = """
State Temperature Pressure Density Specific weight
[K] [°C] [°F] [MPa] [bara] [psia] [mol/dm3] [g/l,] [kg/m3] [lbm/ft3] [sl/ft3*10-3 ] [N/m3] [lbf/ft3]
Liquid at equilibrium pressure
13.96 -259.2 -434.5 0.00770 0.0770 1.12 38.15 76.91 4.801 149.2 754.2 4.801
14 -259 -434 0.00789 0.0789 1.14 38.13 76.87 4.799 149.1 753.8 4.799
16 -257 -431 0.0215 0.215 3.12 37.26 75.12 4.689 145.8 736.7 4.689
18 -255 -427 0.0481 0.481 6.97 36.32 73.22 4.571 142.1 718.1 4.571
20 -253 -424 0.0932 0.932 13.5 35.27 71.11 4.439 138.0 697.4 4.439
22 -251 -420 0.163 1.63 23.7 34.09 68.73 4.291 133.4 674.0 4.291
24 -249 -416 0.264 2.64 38.3 32.74 66.00 4.120 128.1 647.2 4.120
26 -247 -413 0.403 4.03 58.4 31.15 62.80 3.921 121.9 615.9 3.921
28 -245 -409 0.585 5.85 84.9 29.23 58.92 3.678 114.3 577.8 3.678
30 -243 -406 0.850 8.50 123 26.71 53.84 3.361 104.5 528.0 3.361
32 -241 -402 1.12 11.2 162 22.64 45.64 2.849 88.55 447.5 2.849
33.19 -240.0 -399.9 1.33 13.3 193 14.94 30.12 1.880 58.44 295.4 1.880
"""

data_gas = """
State Temperature Pressure Density Specific weight
[K] [°C] [°F] [MPa] [bara] [psia] [mol/dm3] [g/l,] [kg/m3] [lbm/ft3] [sl/ft3*10-3 ] [N/m3] [lbf/ft3]
Gas at equilibrium pressure
13.96	-259.2	-434.5	0.00770	0.0770	1.12	0.06754	0.1362	8.50E-03	0.2642	1.335	8.50E-03
14	-259	-434	0.00789	0.0789	1.14	0.06902	0.1391	8.69E-03	0.2700	1.365	8.69E-03
16	-257	-431	0.0215	0.215	3.12	0.1676	0.3380	0.02110	0.6558	3.314	0.02110
18	-255	-427	0.0481	0.481	6.97	0.3413	0.6880	0.04295	1.335	6.747	0.04295
20	-253	-424	0.0932	0.932	13.5	0.6165	1.243	0.07759	2.412	12.19	0.07759
22	-251	-420	0.163	1.63	23.7	1.025	2.067	0.1290	4.010	20.27	0.1290
24	-249	-416	0.264	2.64	38.3	1.609	3.244	0.2025	6.294	31.81	0.2025
26	-247	-413	0.403	4.03	58.4	2.431	4.900	0.3059	9.508	48.06	0.3059
28	-245	-409	0.585	5.85	84.9	3.600	7.258	0.4531	14.08	71.18	0.4531
30	-243	-406	0.850	8.50	123	5.364	10.81	0.6751	20.98	106.1	0.6751
32	-241	-402	1.12	11.2	162	8.682	17.50	1.093	33.96	171.7	1.093
33.19	-240.0	-399.9	1.33	13.3	193	14.94	30.12	1.880	58.44 295.4	1.880
"""

df_liquid = parse_table(data_liquid)
df_gas = parse_table(data_gas)

import matplotlib.pyplot as plt
import aerosandbox.tools.pretty_plots as p

fig, ax = plt.subplots(figsize=(4.5,5))
p.plot_smooth(
    df_liquid["Temperature_K"],
    df_liquid["Density_kg_m3"],
    "-", label="Liquid",
)
p.plot_smooth(
    df_gas["Temperature_K"],
    df_gas["Density_kg_m3"],
    "-", label="Gas",
)

p.vline(
    22,
    text="Tank conditions (22 K)",
)

plt.annotate(
    text="Critical Point", # last point in the liquid data
    xy=(df_liquid["Temperature_K"].iloc[-1], df_liquid["Density_kg_m3"].iloc[-1]),
    xytext=(-25, -10),
    textcoords="offset points",
    ha="right",
    va="center",
    arrowprops={
        "color"     : "k",
        "width"     : 0.25,
        "headwidth" : 4,
        "headlength": 6,
    }
)


plt.ylim(bottom=0)

p.show_plot(
    "Hydrogen Phase Density by Temperature\nat Liquid-Gas Equilibrium",
    "Temperature [K]",
    "Density [kg/m$^3$]",
)