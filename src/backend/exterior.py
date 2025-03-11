from .trackable import Trackable
from ..nestconf import Configurable


class Exterior(Configurable, Trackable):
    # Configuration fields defined directly in the class
    pH: float = 7.2

    # Non-config fields
    TRACKABLE_FIELDS = ('pH',)

    def __init__(self,
                 *,
                 display_name: str = None,
                 **kwargs):
        # Initialize both parent classes with their required parameters
        super().__init__(**kwargs)  # This will handle both Configurable and Trackable initialization
        self.pH = self.pH  # Initialize from config value
