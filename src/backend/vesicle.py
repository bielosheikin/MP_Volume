import math
import numpy as np
from backend.trackable import Trackable
from backend.constants import FARADAY_CONSTANT
from nestconf import Configurable


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
                 **kwargs):
        Configurable.__init__(self, **kwargs)
        Trackable.__init__(self, display_name=display_name)

        self.init_volume = (4 / 3) * math.pi * (self.init_radius ** 3)
        self.volume = self.init_volume

        self.init_area = 4.0 * math.pi * (self.init_radius ** 2)
        self.area = self.init_area

        self.init_capacitance = self.init_area * self.specific_capacitance
        self.capacitance = self.area * self.specific_capacitance

        self.init_charge = self.init_voltage * self.init_capacitance
        self.charge = self.init_voltage * self.capacitance

        self.pH = self.init_pH
        self.voltage = self.init_voltage