import numpy as np
import matplotlib.pyplot as plt
import myokit
import myokit.lib.plots

# Declarations
filename = 'models/difrancesco_noble_1985'
figsize = (6, 4)

model = myokit.load_model(f'{filename}_osmo.mmt')
protocol = None  # Sino-atrial model so no pacing needed

sim = myokit.Simulation(model, protocol=protocol)
log = sim.run(5)  # Time in units of s not ms

# Plot membrane voltage
plt.figure(figsize=figsize, layout='tight')
plt.plot(log.time(), log['membrane.V'])
plt.title('AP trace')
plt.xlabel('Time (s)')
plt.ylabel('Voltage (mV)')
plt.savefig('figures/ap-trace.png', dpi=300)
plt.show()

# Plot the steady steady missing concentration
plt.figure(figsize=figsize, layout='tight')
plt.plot(log.time(), log['osmosis.missing_conc'])
plt.title('Missing Concentration for Steady State')
plt.ylabel('Missing  Intracellular Concentration (mM)')
plt.xlabel('Time (s)')
plt.savefig('figures/missing_conc.png', dpi=300)
plt.show()

# Plot the cell volume
plt.figure(figsize=figsize, layout='tight')
plt.plot(log.time(), log['osmosis.steady_vol'])
plt.title('Steady State Cell Volume')
plt.ylabel('Volume')
plt.xlabel('Time (s)')
plt.savefig('figures/volume.png', dpi=300)
plt.show()

# List of concentrations
intra = [f'intracellular_{a}_concentration.{b}' for a, b in
         [('sodium', 'Nai'), ('calcium', 'Cai'), ('potassium', 'Ki')]]
extra = ['extracellular_potassium_concentration.Kc']

# Concentration plot
labels = intra+extra+['osmosis.missing_conc']
labels = [i.split('.')[-1] for i in labels]
plt.figure(figsize=figsize, layout='tight')
myokit.lib.plots.cumulative_current(log, intra+extra+['osmosis.missing_conc'], labels=labels, line_args={'lw': 0})
plt.legend()
plt.title('Ionic Concentrations')
plt.ylabel('Extracellular (mM) <---> Intracellular (mM)')
plt.xlabel('Time (s)')
plt.savefig('figures/concentrations.png', dpi=300)
plt.show()
