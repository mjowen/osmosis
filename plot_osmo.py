import numpy as np
import matplotlib.pyplot as plt
import myokit
import myokit.lib.plots
import myokit.lib.guess

# Declarations
filename = 'models/ToRORd_dynCl_mid'
figsize = (6, 4)

# List of concentrations
if 'difrancesco_noble' in filename:
    intra = [f'intracellular_{a}_concentration.{b}' for a, b in
             [('sodium', 'Nai'), ('calcium', 'Cai'), ('potassium', 'Ki')]]
    extra = ['extracellular_potassium_concentration.Kc']
    timeunits = 1 #s
elif 'ToRORd' in filename:
    intra = [f'intracellular_ions.{a}' for a in ['nai', 'ki', 'cai', 'cli']]
    extra = [f'extracellular.{a}' for a in ['nao', 'ko', 'cao', 'clo']]
    timeunits = 1000 #ms
else:
    intra = []
    extra = []
    timeunits = 1000 #ms

model = myokit.load_model(f'{filename}_osmo.mmt')
if 'difrancesco_noble' in filename:
    protocol = None  # Sino-atrial model so no pacing needed
else:
    protocol = myokit.pacing.blocktrain(1*timeunits, 1)

sim = myokit.Simulation(model, protocol=protocol)
log = sim.run(5*timeunits)

# Plot membrane voltage
plt.figure(figsize=figsize, layout='tight')
plt.plot(log.time(), log[myokit.lib.guess.membrane_potential(model).qname()])
plt.title('AP trace')
plt.xlabel('Time (s)')
plt.ylabel('Voltage (mV)')
plt.savefig(f'figures/{filename.split("/")[-1]}-ap-trace.png', dpi=300)
plt.show()

# Plot the steady steady missing concentration
plt.figure(figsize=figsize, layout='tight')
plt.plot(log.time(), log['osmosis.missing_conc'])
plt.title('Missing Concentration for Steady State')
plt.ylabel('Missing  Intracellular Concentration (mM)')
plt.xlabel('Time (s)')
plt.savefig(f'figures/{filename.split("/")[-1]}-missing_conc.png', dpi=300)
plt.show()

# Plot the cell volume
plt.figure(figsize=figsize, layout='tight')
plt.plot(log.time(), log['osmosis.steady_vol'])
plt.title('Steady State Cell Volume')
plt.ylabel('Volume')
plt.xlabel('Time (s)')
plt.savefig(f'figures/{filename.split("/")[-1]}-volume.png', dpi=300)
plt.show()

# Concentration plot
# If any concentrations are fixed as variables (likely for the extracellular ions), they need to be added to the log so that myokit doesn't get confused trying to plot them.
labels = intra+extra+['osmosis.missing_conc']
for i in labels:
    if i not in log.keys():
        log[i] = [model.get(i).value()]*len(log.time())
# Extracellular ions should appear as negative
for i in extra:
    log[i] = -1*np.array(log[i])
labels = [i.split('.')[-1] for i in labels]
plt.figure(figsize=figsize, layout='tight')
myokit.lib.plots.cumulative_current(log, intra+extra+['osmosis.missing_conc'], labels=labels, line_args={'lw': 0})
plt.legend()
plt.title('Ionic Concentrations')
plt.ylabel('Extracellular (mM) <---> Intracellular (mM)')
plt.xlabel('Time (s)')
plt.savefig(f'figures/{filename.split("/")[-1]}-concentrations.png', dpi=300)
plt.show()
