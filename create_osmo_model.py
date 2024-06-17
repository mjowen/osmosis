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


def create_osmo_model(model, intra, extra, filename=None):
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
    filename : str, optional
        The filename to save the model under. If the filename is not provided, the model is not saved.
    """
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


if __name__ == '__main__':
    filenames = ['models/ToRORd_dynCl_mid', 'models/difrancesco_noble_1985']
    for filename in filenames:
        if 'difrancesco_noble' in filename:
            intra = [f'intracellular_{a}_concentration.{b}' for a, b in
                     [('sodium', 'Nai'), ('calcium', 'Cai'), ('potassium', 'Ki')]]
            extra = ['extracellular_potassium_concentration.Kc']
        elif 'ToRORd' in filename:
            intra = [f'intracellular_ions.{a}' for a in ['nai', 'ki', 'cai', 'cli']]
            extra = [f'extracellular.{a}' for a in ['nao', 'ko', 'cao', 'clo']]
        else:
            intra = []
            extra = []
        model = convert_to_myokit(filename)
        create_osmo_model(model, intra, extra, filename)
