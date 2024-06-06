import myokit
import numpy as np

# Declarations
filename = 'difrancesco_noble_1985'

# Import cellml file
i = myokit.formats.importer('cellml')
model = i.model(f'{filename}.cellml')

# Add bindings
model.var('membrane.i_pulse').set_binding('pace')

# Save as .mmt file
myokit.save(filename=f'{filename}.mmt', model=model)

# List of concentrations
intra = [f'intracellular_{a}_concentration.{b}' for a, b in
         [('sodium', 'Nai'), ('calcium', 'Cai'), ('calcium', 'Ca_up'), ('calcium', 'Ca_rel'), ('calcium', 'p'),
          ('potassium', 'Ki')]]
extra = ['extracellular_potassium_concentration.Kc']

# Calculate initial osmolarity
initial_intra = [model.get(i).initial_value(as_float=True) for i in intra]
initial_extra = [model.get(i).initial_value(as_float=True) for i in extra]
initial_missing = np.sum(initial_extra) - np.sum(initial_intra)
if initial_missing > 0:
    print(f'Missing intracellular concentration of {initial_missing}')
else:
    print(f'Missing extracellular concentration of {-initial_missing}')

# Add in osmosis module
code = model.code()
osmo_code = code + f"""[osmosis]
intra = {' + '.join(intra)}
extra = {' + '.join(extra)}
missing_conc = extra - intra
init_missing = {initial_missing}
steady_vol = (init_missing + intra)/extra
"""

osmo_model = myokit.parse_model(osmo_code)
myokit.save(f'{filename}_osmo.mmt', osmo_model)
