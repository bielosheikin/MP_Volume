from backend.trackable import Trackable
from nestconf import Configurable


class Exterior(Configurable, Trackable):
    # Configuration fields defined directly in the class
    pH: float = 7.2
    display_name: str = "Exterior"  # Add display_name as a config field with default value

    # Non-config fields
    TRACKABLE_FIELDS = ('pH',)

    def __init__(self,
                 *,
                 display_name: str = None,
                 **kwargs):
        # Initialize both parent classes with their required parameters
        if display_name is not None:
            kwargs['display_name'] = display_name
        super().__init__(**kwargs)  # This will handle both Configurable and Trackable initialization
        self.pH = self.pH  # Initialize from config value
