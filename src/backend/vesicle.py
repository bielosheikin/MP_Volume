import math
from .trackable import Trackable
from .constants import FARADAY_CONSTANT


class VesicleConfig:
    DEFAULT_SPECIFIC_CAPACITANCE = 1e-2
    DEFAULT_INIT_VOLTAGE = 4e-2
    DEFAULT_INIT_RADIUS = 1.3e-6
    DEFAULT_INIT_PH = 7.4

    def __init__(self,
                 *,
                 specific_capacitance: float = None,
                 init_voltage: float = None,
                 init_radius: float = None,
                 init_pH: float = None
                 ):
        
        self.specific_capacitance = specific_capacitance if specific_capacitance is not None else self.DEFAULT_SPECIFIC_CAPACITANCE
        self.init_voltage = init_voltage if init_voltage is not None else self.DEFAULT_INIT_VOLTAGE
        self.voltage = self.init_voltage
        self.init_radius = init_radius if init_radius is not None else self.DEFAULT_INIT_RADIUS

        self.init_pH = init_pH if init_pH is not None else self.DEFAULT_INIT_PH


class Vesicle(Trackable):
    TRACKABLE_FIELDS = ('pH', 'volume', 'area', 'capacitance', 'charge', 'voltage')

    def __init__(self,
                 *,
                 config: VesicleConfig = None,
                 init_buffer_capacity: float = None,
                 **kwargs):
        super(Vesicle, self).__init__(**kwargs)

        self.config = config if config is not None else VesicleConfig()

        self.init_volume = (4 / 3) * math.pi * (self.config.init_radius ** 3)
        self.volume = self.init_volume

        self.init_area = 4.0 * math.pi * (self.config.init_radius ** 2)
        self.area = self.init_area

        self.init_capacitance = self.init_area * self.config.specific_capacitance
        self.capacitance = self.area * self.config.specific_capacitance

        self.init_charge = self.config.init_voltage * self.init_capacitance
        self.charge = self.config.voltage * self.capacitance

        self.pH = self.config.init_pH
        self.voltage = self.config.init_voltage