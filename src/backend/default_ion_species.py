from .ion_species import IonSpecies

default_ion_species = {
    "cl": IonSpecies(
        display_name='cl',
        init_vesicle_conc=159 * 1e-3,
        exterior_conc=20 * 1e-3,
        elementary_charge=-1
    ),
    "h": IonSpecies(
        display_name='h',
        init_vesicle_conc=7.962143411069938 * 1e-5,
        exterior_conc=12.619146889603859 * 1e-5,
        elementary_charge=1
    ),
    "na": IonSpecies(
        display_name='na',
        init_vesicle_conc=150 * 1e-3,
        exterior_conc=10 * 1e-3,
        elementary_charge=1
    ),
    "k": IonSpecies(
        display_name='k',
        init_vesicle_conc=5 * 1e-3,
        exterior_conc=140 * 1e-3,
        elementary_charge=1
    )
}