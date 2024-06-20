import myokit
import numpy as np


def convert_to_myokit(filename):
    """
    Convert a cellml file to a myokit file. The cellml file is found using filename + '.cellml'. The myokit model is saved as filename + '.mmt' and returned.

    Parameters
    ----------
    filename : str
        Name of the file to convert.
    Returns
    -------
    model : myokit.Model
        Myokit model.
    """
    # Import cellml file
    i = myokit.formats.importer('cellml')
    model = i.model(f'{filename}.cellml')

    # Save as .mmt file
    myokit.save(filename=f'{filename}.mmt', model=model)
    return model


def create_osmo_model(model, intra, extra, volume, filename=None):
    """
    Create a new myokit model with the osmosis module added. This module calculates the osmolarity of the cell and the volume of the cell. The model is saved as filename + '_osmo.mmt'.

    Parameters
    ----------
    model : myokit.Model
        Myokit model to add the osmosis module to.
    intra : list
        List of strings for the myokit qnames of the intracellular concentrations.
    extra : list
        List of strings for the myokit qnames of the extracellular concentrations.
    volume : str
        Myokit qname for the volume of the cell.
    filename : str, optional
        The filename to save the model under. If the filename is not provided, the model is not saved.
    """
    # Convert concentrations to state variables
    for i in intra + extra:
        if not model.get(i).is_state():
            model.get(i).promote(initial_value=model.get(i).value())
            model.get(i).set_rhs(f'0 [mM/{str(model.time_unit())[1:-1]}]')

    # Calculate initial osmolarity
    initial_intra = [model.get(i).initial_value(as_float=True) for i in intra]
    initial_extra = [model.get(i).initial_value(as_float=True) for i in extra]
    initial_missing = np.sum(initial_extra) - np.sum(initial_intra)
    if initial_missing > 0:
        print(f'Missing intracellular concentration of {initial_missing}')
    else:
        print(f'Missing extracellular concentration of {-initial_missing}')

    # Add in osmosis module
    # Initial volume is 2000um^3=2e-9mL
    code = model.code()
    if initial_missing > 0:
        component = f"""[osmosis]
intra = {' + '.join(intra)}
    in [mmol]
extra = {' + '.join(extra)}
    in [mM]
missing_conc = extra - intra/steady_volume
    in [mM]
init_missing = {initial_missing} [mM]
    in [mM]
init_volume = 2e-9 [L]
    in [L]
steady_volume = (init_missing*init_volume + intra)/extra
   in [L]
"""
    else:
        component = f"""[osmosis]
intra = {' + '.join(intra)}
    in [mmol]
extra = {' + '.join(extra)}
    in [mM]
missing_conc = extra - intra/steady_volume
    in [mM]
init_missing = {initial_missing} [mM]
    in [mM]
init_volume = 2e-9 [L]
    in [L]
steady_volume = intra/(extra-init_missing)
    in [L]
"""

    osmo_code = code + component

    osmo_model = myokit.parse_model(osmo_code)

    # Replace intracellular concentrations with quantities
    for i in intra:
        osmo_model.get(i).set_initial_value(osmo_model.get(i).initial_value(as_float=True)*osmo_model.get('osmosis.init_volume').value())
        osmo_model.get(i).set_unit('mmol')
        rhs = str(osmo_model.get(i).rhs())
        # Remove any uses of the fixed volume
        osmo_model.get(i).set_rhs(rhs.replace(volume, '1 [1]'))

    # Replace uses of concentrations with concentrations calculated through the quantities
    for i in intra:
        for j in osmo_model.get(i).refs_by(state_refs=True):
            if 'osmosis' not in j.qname():
                rhs = str(j.rhs())
                rhs = rhs.replace(i, f'({i}/{osmo_model.get("osmosis.steady_volume").qname()})')
                j.set_rhs(rhs)

    myokit.save(f'{filename}_osmo.mmt', osmo_model)


if __name__ == '__main__':
    filenames = ['models/ToRORd_dynCl_mid', 'models/difrancesco_noble_1985']
    for filename in filenames:
        if 'difrancesco_noble' in filename:
            intra = [f'intracellular_{a}_concentration.{b}' for a, b in
                     [('sodium', 'Nai'), ('calcium', 'Cai'), ('potassium', 'Ki')]]
            extra = ['extracellular_potassium_concentration.Kc', 'extracellular_sodium_concentration.Nao',
                     'extracellular_calcium_concentration.Cao']
            volume = 'intracellular_sodium_concentration.Vi'
        elif 'ToRORd' in filename:
            intra = [f'intracellular_ions.{a}' for a in ['nai', 'ki', 'cai', 'cli']]
            extra = [f'extracellular.{a}' for a in ['nao', 'ko', 'cao', 'clo']]
            volume = 'cell_geometry.vmyo'
        else:
            intra = []
            extra = []
            volume = ''
        model = convert_to_myokit(filename)
        create_osmo_model(model, intra, extra, volume, filename)
