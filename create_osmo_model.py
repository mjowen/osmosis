import myokit
import numpy as np

# Declarations
filename = 'models/ToRORd_dynCl_mid'

# Import cellml file
i = myokit.formats.importer('cellml')
model = i.model(f'{filename}.cellml')

# Save as .mmt file
myokit.save(filename=f'{filename}.mmt', model=model)

# List of concentrations
if 'difrancesco_noble' in filename:
    intra = [f'intracellular_{a}_concentration.{b}' for a, b in
             [('sodium', 'Nai'), ('calcium', 'Cai'), ('potassium', 'Ki')]]
    extra = ['extracellular_potassium_concentration.Kc']
elif 'ToRORd' in filename:
    intra = [f'intracellular_ions.{a}' for a in ['nai', 'ki', 'cai', 'cli']]
    extra = [f'extracellular.{a}' for a in ['nao', 'ko', 'cao', 'clo']]

# Calculate initial osmolarity
initial_intra = [model.get(i).initial_value(as_float=True) for i in intra]
# Extracellular may be stored as states (so initial values work) or as variables (so initial value won't work)
try:
    initial_extra = [model.get(i).initial_value(as_float=True) for i in extra]
except Exception as e:
    if 'Only state variables have initial values.' in str(e):
        initial_extra = [model.get(i).value() for i in extra]
    else:
        raise e

initial_missing = np.sum(initial_extra) - np.sum(initial_intra)
if initial_missing > 0:
    print(f'Missing intracellular concentration of {initial_missing}')
else:
    print(f'Missing extracellular concentration of {-initial_missing}')

# Add in osmosis module
code = model.code()
if initial_missing > 0:
    component = f"""[osmosis]
intra = {' + '.join(intra)}
extra = {' + '.join(extra)}
missing_conc = extra - intra
init_missing = {initial_missing}
steady_vol = (init_missing + intra)/extra
"""
else:
    component = f"""[osmosis]
intra = {' + '.join(intra)}
extra = {' + '.join(extra)}
missing_conc = extra - intra
init_missing = {initial_missing}
steady_vol = intra/(extra-init_missing)
"""

osmo_code = code + component

osmo_model = myokit.parse_model(osmo_code)
myokit.save(f'{filename}_osmo.mmt', osmo_model)
