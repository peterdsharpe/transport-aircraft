# from solve import *
from scipy import stats
from numba import njit

### Point Estimate
demand_100_pax_km = 8.053e9 # pax-km / day
FC_pax_km = 5.83e-3

m_lh2_kg_per_day = demand_100_pax_km * FC_pax_km

l_f = 0.0002 * 1e-2
l_d = 0.05 * 1e-2
l_s = 0.035 * 1e-2

P_l = (
              (1 + l_f) *
              (1 + l_d) *
              (1 + l_s)
      ) - 1

SEC_e_kWh_per_kg = 50
SEC_l_kWh_per_kg = 11.9

E_kWh_per_day = (
        m_lh2_kg_per_day *
        (1 + P_l) *
        (SEC_e_kWh_per_kg + SEC_l_kWh_per_kg)
)  # kWh/day

E_watts = E_kWh_per_day * (u.kilo * u.hour / u.day)
E_TWh_per_day = E_kWh_per_day / 1e9

print(E_TWh_per_day)


#
# @njit
# def get_power():
#     demand_100_pax_km = 5e9 * np.random.lognormal(0, 0.05) # pax-km / day
#
#     # FC_pax_km = s(mass_props['fuel'].mass / (n_pax * (flight_range / u.kilo)))
#     FC_pax_km = 5.83e-3 * np.random.lognormal(0, 6.21 / 5.83 - 1)
#
#     m_lh2_kg_per_day = demand_100_pax_km * FC_pax_km
#
#     l_f = 0.0002 * 1e-2 * np.random.rand()
#     l_d = 0.05 * 1e-2 * np.random.rand()
#     l_s = 0.035 * 1e-2
#
#     P_l = (
#                   (1 + l_f) *
#                   (1 + l_d) *
#                   (1 + l_s)
#           ) - 1
#
#     SEC_e_kWh_per_kg = np.random.uniform(45, 78)
#     SEC_l_kWh_per_kg = np.random.uniform(11.9, 15)
#
#     E_kWh_per_day = (
#             m_lh2_kg_per_day *
#             (1 + P_l) *
#             (SEC_e_kWh_per_kg + SEC_l_kWh_per_kg)
#     )  # kWh/day
#
#     E_watts = E_kWh_per_day * (u.kilo * u.hour / u.day)
#     E_TWh_per_year = E_kWh_per_day / 1e9 * (u.year / u.day)
#
#     return E_TWh_per_year
#
#
# E_TWh_per_year_dist = np.array([
#     get_power()
#     for _ in range(100000)
# ])
#
# import matplotlib.pyplot as plt
# import aerosandbox.tools.pretty_plots as p
#
# fig, ax = plt.subplots(figsize=(4.5, 3))
#
# p.sns.kdeplot(
#     E_TWh_per_year_dist,
#     fill=True,
#     # kind='kde',
#     legend=False,
#     log_scale=True,
#     bw_adjust=3
# )
# plt.xscale('linear')
#
# p.vline(
#     E_TWh_per_year,
#     text=f"Point Estimate\n({E_TWh_per_year:.0f} TWh/yr)",
#     text_kwargs=dict(
#         fontsize=10
#     )
# )
#
# plt.xlim(left=0, right=1400)
# p.set_ticks(200, 100)
# plt.ylabel("Relative Likelihood")
# p.show_plot(
#     "Probability Distribution of Global Electricity Needs",
#     "Required Global Electricity Production\nfor 100-Airport Network [TWh/year]",
#     savefig="figures/network_scale.svg"
# )
