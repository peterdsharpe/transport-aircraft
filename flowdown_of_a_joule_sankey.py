from solve import *
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

# E_TWh_per_day = 0.0445
# m_lh2_kg_per_day = 0.719e6


SEC_e_kWh_per_kg_ideal = 141.80e6 / 3600 / 1e3 # Comes from specific heat of formations
SEC_l_kWh_per_kg_ideal = 3.9 # https://www.hydrogen.energy.gov/pdfs/9013_energy_requirements_for_hydrogen_gas_compression.pdf

#### Sankey
propulsion_input = m_lh2_kg_per_day * fuel_specific_energy / 1e12 / 3600

# Go down into airplane
propulsive_efficiency = s(dyn.speed * Isp * 9.81 / fuel_specific_energy)
propulsion_losses = (1 - propulsive_efficiency) * propulsion_input

air_input = propulsive_efficiency * propulsion_input

# Go up into network
storage_losses = propulsion_input * (1 - 1 / (1 + P_l))
storage_input = propulsion_input + storage_losses

liquefaction_input = m_lh2_kg_per_day * (1 + P_l) * SEC_l_kWh_per_kg / 1e9

electrolyzer_losses = E_TWh_per_day * (
    (SEC_e_kWh_per_kg - SEC_e_kWh_per_kg_ideal) / (SEC_e_kWh_per_kg)
)

electrolyzer_input = m_lh2_kg_per_day * (1 + P_l) * SEC_e_kWh_per_kg / 1e9
electrolyzer_input_ideal = m_lh2_kg_per_day * (1 + P_l) * SEC_e_kWh_per_kg_ideal / 1e9

liquefaction_losses = liquefaction_input *(
    (SEC_l_kWh_per_kg - SEC_l_kWh_per_kg_ideal) / SEC_l_kWh_per_kg
)

# storage_input = liquefaction_input - liquefaction_losses

# storage_losses = P_l * storage_input


# propulsion_input = storage_input - storage_losses



