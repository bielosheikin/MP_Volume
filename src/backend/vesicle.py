import math
import numpy as np
from .trackable import Trackable
from .constants import FARADAY_CONSTANT
from ..nestconf import Configurable
from typing import Optional


class Vesicle(Configurable, Trackable):
    # Configuration fields defined directly in the class
    specific_capacitance: float = 1e-2
    init_voltage: float = 4e-2
    init_radius: float = 1.3e-6
    init_pH: float = 7.4

    # Non-config fields
    TRACKABLE_FIELDS = ('pH', 'volume', 'area', 'capacitance', 'charge', 'voltage')

    def __init__(self,
                 *,               
                 display_name: str = None,
                 init_voltage: Optional[float] = None,
                 **kwargs):
        Configurable.__init__(self, **kwargs)
        Trackable.__init__(self, display_name=display_name)

        # Use typical values for voltage_exponent and half_act_voltage
        voltage_exponent = 80.0
        half_act_voltage = -0.04
        MAX_VOLTAGE = 709 / voltage_exponent + half_act_voltage

        # Clamp init_voltage if it exceeds the calculated safe limit
        if init_voltage is not None:
            if init_voltage > MAX_VOLTAGE:
                print(f"Warning: init_voltage {init_voltage} exceeds the safe limit. Clamping to {MAX_VOLTAGE}.")
                init_voltage = MAX_VOLTAGE
            elif init_voltage < -MAX_VOLTAGE:
                print(f"Warning: init_voltage {init_voltage} is below the negative safe limit. Clamping to {-MAX_VOLTAGE}.")
                init_voltage = -MAX_VOLTAGE
        else:
            init_voltage = self.init_voltage

        self.init_volume = (4 / 3) * math.pi * (self.init_radius ** 3)
        self.volume = self.init_volume

        self.init_area = 4.0 * math.pi * (self.init_radius ** 2)
        self.area = self.init_area

        self.init_capacitance = self.init_area * self.specific_capacitance
        self.capacitance = self.area * self.specific_capacitance

        self.init_charge = init_voltage * self.init_capacitance
        self.charge = init_voltage * self.capacitance

        self.pH = self.init_pH
        self.voltage = init_voltage