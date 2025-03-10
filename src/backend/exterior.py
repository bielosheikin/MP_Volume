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
        Configurable.__init__(self, **kwargs)
        Trackable.__init__(self, display_name=display_name)
        self.pH = self.pH  # Initialize from config value
