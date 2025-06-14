from .ion_channels import IonChannel

default_channels = {
    "asor": IonChannel(
        conductance=8e-5,
        channel_type='wt',
        dependence_type='voltage_and_pH',
        voltage_multiplier=1,
        nernst_multiplier=1,
        voltage_shift=0,
        flux_multiplier=1,
        allowed_primary_ion='cl',
        primary_exponent=1,
        voltage_exponent=80.0,
        half_act_voltage=-0.04,
        pH_exponent=3.0,
        half_act_pH=5.4,
        display_name='ASOR'
    ),
    "clc": IonChannel(
        conductance=1e-7,
        channel_type='clc',
        dependence_type='voltage_and_pH',
        voltage_multiplier=1,
        nernst_multiplier=1 / 3,
        voltage_shift=0,
        flux_multiplier=2,
        allowed_primary_ion='cl',
        allowed_secondary_ion='h',
        primary_exponent=2,
        secondary_exponent=1,
        voltage_exponent=80.0,
        half_act_voltage=-0.04,
        pH_exponent=-1.5,
        half_act_pH=5.5,
        use_free_hydrogen=True,
        coupled_channels=['clc_h'],
        display_name='CLC'
    ),
    "tpc": IonChannel(
        conductance=2e-6,
        dependence_type=None,
        voltage_multiplier=-1,
        nernst_multiplier=1,
        voltage_shift=0,
        flux_multiplier=1,
        allowed_primary_ion='na',
        primary_exponent=1,
        display_name='TPC'
    ),
    "nhe": IonChannel(
        conductance=0.0,
        dependence_type=None,
        voltage_multiplier=0,
        nernst_multiplier=1,
        voltage_shift=0,
        flux_multiplier=1,
        allowed_primary_ion='na',
        allowed_secondary_ion='h',
        custom_nernst_constant=1,
        primary_exponent=1,
        secondary_exponent=1,
        use_free_hydrogen=True,
        coupled_channels=['nhe_h'],
        display_name='NHE'
    ),
    "vatpase": IonChannel(
        conductance=8e-9,
        dependence_type='time',
        voltage_multiplier=1,
        nernst_multiplier=-1,
        voltage_shift=0.27,
        flux_multiplier=-1,
        allowed_primary_ion='h',
        primary_exponent=1,
        time_exponent=0.0,
        half_act_time=0.0,
        display_name='VATPase'
    ),
    "clc_h": IonChannel(
        # Coupling-specific parameters
        flux_multiplier=-1,
        primary_exponent=1,
        secondary_exponent=2,
        is_coupled_channel=True,
        master_channel_name='clc',
        display_name='CLC_H'
        # All other parameters will be synchronized from the master 'clc' channel
    ),
    "nhe_h": IonChannel(
        # Coupling-specific parameters
        flux_multiplier=-1,
        is_coupled_channel=True,
        master_channel_name='nhe',
        display_name='NHE_H'
        # All other parameters will be synchronized from the master 'nhe' channel
    ),
    "hleak": IonChannel(
        conductance=1.6e-8,
        dependence_type=None,
        voltage_multiplier=-1,
        nernst_multiplier=1,
        voltage_shift=0,
        flux_multiplier=1,
        allowed_primary_ion='h',
        primary_exponent=1,
        use_free_hydrogen=True,
        display_name='HLeak'
    ),
    "k_channel": IonChannel(
        conductance=0.0,
        dependence_type=None,
        voltage_multiplier=-1,
        nernst_multiplier=1,
        voltage_shift=0,
        flux_multiplier=1,
        allowed_primary_ion='k',
        primary_exponent=1,
        display_name='K'
    )
}

def synchronize_default_coupled_channels():
    """
    Synchronize coupled channels with their master channels.
    This should be called after all default channels are created.
    """
    for channel_name, channel in default_channels.items():
        if channel.is_coupled_channel and channel.master_channel_name:
            master_channel = default_channels.get(channel.master_channel_name)
            if master_channel:
                channel.sync_from_master(master_channel)

# Synchronize coupled channels on module load
synchronize_default_coupled_channels()